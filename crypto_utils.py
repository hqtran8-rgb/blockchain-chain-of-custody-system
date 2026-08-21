from Crypto.Cipher import AES
import struct
import uuid
# simple AES key used for UUID/item encryption in this project
AES_KEY = b"R0chLi4uLi4uLi4="


def encrypt_case_id(case_uuid):
    # accept both UUID objects and strings 
    if isinstance(case_uuid, str):
        case_uuid = uuid.UUID(case_uuid)

    uuid_bytes = case_uuid.bytes
    # AES-ECB used for fixd 16-byte UUIDs
    cipher = AES.new(AES_KEY, AES.MODE_ECB)

    encrypted = cipher.encrypt(uuid_bytes)
    # stored as ACII hex for consistency with block format
    return encrypted.hex().encode('ascii')


def decrypt_case_id(encrypted_bytes):
    # handle INITIAL black case_id = 000...0
    if encrypted_bytes == b'0' * 32:
        return uuid.UUID('00000000-0000-0000-0000-000000000000')
    # decode AES-encrypted hex into 16 raw bytes 
    if len(encrypted_bytes) == 32 and all(c in b'0123456789abcdef' for c in encrypted_bytes):
        encrypted_uuid = bytes.fromhex(encrypted_bytes.decode('ascii'))
    else:
        encrypted_uuid = encrypted_bytes[:16]

    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_uuid)
    # reconstruct UUID object 
    return uuid.UUID(bytes=decrypted)


def encrypt_item_id(item_id):
    # item IDs stored as big-endian 4 bytes
    item_bytes = struct.pack('>I', item_id)
    # pad to 16 bytes for AES block size 
    padded = b'\x00' * 12 + item_bytes

    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(padded)
    # hex encoding for blockchain storage 
    return encrypted.hex().encode('ascii')


def decrypt_item_id(encrypted_bytes):
    # special case for INITIAL block
    if encrypted_bytes == b'0' * 32:
        return 0
    # parse hex-encoded AES block 
    if len(encrypted_bytes) == 32 and all(c in b'0123456789abcdef' for c in encrypted_bytes):
        encrypted_item = bytes.fromhex(encrypted_bytes.decode('ascii'))
    else:
        encrypted_item = encrypted_bytes[:16]
    
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    decrypted = cipher.decrypt(encrypted_item)
    # extract last 4 bytes as original item ID
    item_id = struct.unpack('>I', decrypted[-4:])[0]
    
    return item_id
# simple role-based passwords used throughout UI
VALID_PASSWORDS = {
    'C67C': 'CREATOR',
    'P80P': 'POLICE',
    'L76L': 'LAWYER',
    'A65A': 'ANALYST',
    'E69E': 'EXECUTIVE'
}


def validate_password(password):
    # returns role name if valid, else NOne
    return VALID_PASSWORDS.get(password)


def is_creator_password(password):
    # creator has special privileges
    return password == 'C67C'


def is_owner_password(password):
    # owner refers to anyone with general access roles
    return password in ['P80P', 'L76L', 'A65A', 'E69E']