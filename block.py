import struct
import hashlib
from datetime import datetime
import uuid

class Block:
    #valid lifecycle states for evidence handling 
    VALID_STATES = ['INITIAL', 'CHECKEDIN', 'CHECKEDOUT', 'DISPOSED', 'DESTROYED', 'RELEASED']
    
    def __init__(self, prev_hash, timestamp, case_id, evidence_id, state, 
                 creator='', owner='', data=''):
        #store all block fields
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.case_id = case_id  
        self.evidence_id = evidence_id  
        self.state = state
        self.creator = creator
        self.owner = owner
        self.data = data
    
    def pack(self):
       # convert data to bytes
        if isinstance(self.data, str):
            data_bytes = self.data.encode('utf-8')
        else:
            data_bytes = self.data
        
        data_length = len(data_bytes)
        # pad fixed-length text field
        state_bytes = self.state.encode('utf-8')
        state_padded = state_bytes + b'\x00' * (12 - len(state_bytes))
        
        creator_bytes = self.creator.encode('utf-8')
        creator_padded = creator_bytes + b'\x00' * (12 - len(creator_bytes))
          
        owner_bytes = self.owner.encode('utf-8')
        owner_padded = owner_bytes + b'\x00' * (12 - len(owner_bytes))
        #pack everything into binary format
        header = struct.pack(
            '32s d 32s 32s 12s 12s 12s I',
            self.prev_hash,
            self.timestamp,
            self.case_id,
            self.evidence_id,
            state_padded,
            creator_padded,
            owner_padded,
            data_length
        )
        
        return header + data_bytes
    
    @staticmethod
    def unpack(block_bytes):
        #calculate header size to split bytes correctly
        header_size = struct.calcsize('32s d 32s 32s 12s 12s 12s I')
        
        if len(block_bytes) < header_size:
            raise ValueError("Block data too short")
        #read header fields
        header_data = struct.unpack('32s d 32s 32s 12s 12s 12s I', 
                                    block_bytes[:header_size])
        
        prev_hash = header_data[0]
        timestamp = header_data[1]
        case_id = header_data[2]
        evidence_id = header_data[3]
        state = header_data[4].rstrip(b'\x00').decode('utf-8')
        creator = header_data[5].rstrip(b'\x00').decode('utf-8')
        owner = header_data[6].rstrip(b'\x00').decode('utf-8')
        data_length = header_data[7]
        #read raw data
        data = block_bytes[header_size:header_size + data_length]
        
        return Block(prev_hash, timestamp, case_id, evidence_id, 
                    state, creator, owner, data)
    
    def calculate_hash(self):
        #simple SHA-256 over the packed block
        block_data = self.pack()
        return hashlib.sha256(block_data).digest()
    
    def get_hash_hex(self):
        # return hex for readability 
        return self.calculate_hash().hex()
    
    @staticmethod
    def create_initial_block(timestamp=None):
        #starting block for the chain
        from datetime import datetime
        if timestamp is None:
            timestamp = datetime.utcnow().timestamp()
        
        return Block(
            prev_hash=b'\x00' * 32,
            timestamp=timestamp,
            case_id=b'0' * 32,
            evidence_id=b'0' * 32,
            state='INITIAL',
            creator='',
            owner='',
            data='Initial block\x00'
        )
    
    def __repr__(self):
        #quick view for debugging 
        return (f"Block(state={self.state}, "
                f"timestamp={self.timestamp}, "
                f"creator={self.creator})")