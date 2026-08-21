import os
import struct
from block import Block
from crypto_utils import decrypt_case_id, decrypt_item_id


class Blockchain:
    
    def __init__(self):
        #use enviornment variable if set, otherwise default file name
        self.file_path = os.environ.get('BCHOC_FILE_PATH', 'blockchain.dat')
    
    def file_exists(self):
        # checks whether blockchain file is present 
        return os.path.exists(self.file_path)
    
    def create_initial_block(self):
        # writes the very first block to start the chain
        initial_block = Block.create_initial_block()
        
        with open(self.file_path, 'wb') as f:
            f.write(initial_block.pack())
        
        return True
    
    def has_initial_block(self):
        # validates if file conatins at least one block
        if not self.file_exists():
            return False
        
        try:
            blocks = self.get_all_blocks()

            return len(blocks) > 0
        except:
            return False
    
    def add_block(self, block):
        # append a new block to end of chain
        with open(self.file_path, 'ab') as f:
            f.write(block.pack())
    
    def get_all_blocks(self):
        # reads raw file and reconstructs all blocks in order
        if not self.file_exists():
            return []
        
        blocks = []
        
        with open(self.file_path, 'rb') as f:
            while True:
                header_size = struct.calcsize('32s d 32s 32s 12s 12s 12s I')
                header_bytes = f.read(header_size)
                
                if len(header_bytes) < header_size:
                    break  # stop if end of file reached 
               
                data_length = struct.unpack('I', header_bytes[-4:])[0]
               
                data_bytes = f.read(data_length)
          
                full_block = header_bytes + data_bytes
                block = Block.unpack(full_block)
                blocks.append(block)
        
        return blocks
    
    def get_last_block(self):
        #return most recent block or None  
        blocks = self.get_all_blocks()
        return blocks[-1] if blocks else None
    
    def get_item_blocks(self, item_id_encrypted):
        #filter blocks by specific encrypted item ID 
        blocks = self.get_all_blocks()
        return [b for b in blocks if b.evidence_id == item_id_encrypted]
    
    def get_case_blocks(self, case_id_encrypted):
         #filter blocks by case 
        blocks = self.get_all_blocks()
        return [b for b in blocks if b.case_id == case_id_encrypted]
    
    def item_exists(self, item_id_encrypted):
         # simple existence check for evidence item 
        blocks = self.get_item_blocks(item_id_encrypted)
        return len(blocks) > 0
    
    def get_item_state(self, item_id_encrypted):
        # returns the most recent state transition 
        blocks = self.get_item_blocks(item_id_encrypted)
        if not blocks:
            return None
        return blocks[-1].state 
    
    def verify_chain(self):
        # performs structural and logical checks on entire chain
        blocks = self.get_all_blocks()
        
        if len(blocks) == 0:
            return (False, "No blocks in blockchain", None, None)
        # first block must always be INITIAL 
        if blocks[0].state != 'INITIAL':
            return (False, "Invalid initial block", blocks[0], None)
        
        parent_usage = {}  #tracks how many children each prev_hash has 
        hash_to_block = {} #maps hashes to block objects
        
        for i, block in enumerate(blocks):
            block_hash = block.calculate_hash()
            hash_to_block[block_hash] = block

            if block.prev_hash not in parent_usage:
                parent_usage[block.prev_hash] = []
            parent_usage[block.prev_hash].append(block)
            
            # verify strict linear ordering 
            if i > 0:
                expected_prev_hash = blocks[i-1].calculate_hash()
                if block.prev_hash != expected_prev_hash:
                    # parent missing entirely 
                    if block.prev_hash not in hash_to_block:
                        return (False, "Parent block: NOT FOUND", block, None)
                    else:
                        # parent exists but chain broken
                        return (False, "Block contents do not match block checksum.", 
                               block, blocks[i-1])
        # direct branching 
        for parent_hash, children in parent_usage.items():
            if len(children) > 1 and parent_hash != b'\x00' * 32:
                parent_block = hash_to_block.get(parent_hash)
                return (False, "Two blocks were found with the same parent.", 
                       children[1], parent_block)
        #logical state validation for items  
        item_states = {} 
        
        for i, block in enumerate(blocks):
            if block.state == 'INITIAL':
                continue
            
            item_id = block.evidence_id

            if item_id not in item_states:
                item_states[item_id] = []
            # no actions allowed after disposal/removal states
            if item_states[item_id] and item_states[item_id][-1] in ['DISPOSED', 'DESTROYED', 'RELEASED']:
                return (False, "Item checked out or checked in after removal from chain.", 
                       block, None)
            # duplicate checkin
            if block.state == 'CHECKEDIN' and item_states[item_id] and item_states[item_id][-1] == 'CHECKEDIN':
                return (False, "Item checked in twice without checkout.", 
                       block, blocks[i-1] if i > 0 else None)
            # duplicate checkout
            if block.state == 'CHECKEDOUT' and item_states[item_id] and item_states[item_id][-1] == 'CHECKEDOUT':
                return (False, "Item checked out twice without checkin.", 
                       block, blocks[i-1] if i > 0 else None)
  
            item_states[item_id].append(block.state)
        # if no errors found
        return (True, "CLEAN", None, None)
    
    def get_all_cases(self):
        # returns unique encrypted case IDs
        blocks = self.get_all_blocks()
        cases = set()
        
        for block in blocks:
            if block.state != 'INITIAL':
                cases.add(block.case_id)
        
        return list(cases)
    
    def get_items_for_case(self, case_id_encrypted):
        # lists all evidence items connected to a given case 
        blocks = self.get_case_blocks(case_id_encrypted)
        items = set()
        
        for block in blocks:
            items.add(block.evidence_id)
        
        return list(items)