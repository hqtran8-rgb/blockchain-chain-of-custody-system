import sys
import uuid
from datetime import datetime
from block import Block
from blockchain import Blockchain
from crypto_utils import (
    encrypt_case_id, decrypt_case_id,
    encrypt_item_id, decrypt_item_id,
    validate_password, is_creator_password
)


def cmd_init():
    #set up blockchain file if meissing
    bc = Blockchain()
    
    if not bc.file_exists():
        bc.create_initial_block()
        print("Blockchain file not found. Created INITIAL block.")
        return 0
    # confirms presence of valid initial block
    if bc.has_initial_block():
        print("Blockchain file found with INITIAL block.")
        return 0
    else:
        print("Error: Blockchain file exists but is invalid.")
        return 1


def cmd_add(case_id, item_ids, creator, password):
    # only creator level password allowed here
    if not is_creator_password(password):
        print("Invalid password")
        return 1
    # case must be proper UUID
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        print("Error: Invalid case ID format. Must be a valid UUID.")
        return 1
    
    bc = Blockchain()
    
    if not bc.file_exists():
        bc.create_initial_block()
    
    last_block = bc.get_last_block()
    prev_hash = last_block.calculate_hash()
    #encrypt case for storage
    encrypted_case_id = encrypt_case_id(case_uuid)
    # add each item as its own block
    for item_id in item_ids:
        try:
            item_id_int = int(item_id)
        except ValueError:
            print(f"Error: Invalid item ID: {item_id}")
            return 1
        
        encrypted_item_id = encrypt_item_id(item_id_int)
        # avoid duplicates
        if bc.item_exists(encrypted_item_id):
            print(f"Error: Item ID {item_id_int} already exists in blockchain.")
            return 1
        
        timestamp = datetime.utcnow().timestamp()
        
        new_block = Block(
            prev_hash=prev_hash,
            timestamp=timestamp,
            case_id=encrypted_case_id,
            evidence_id=encrypted_item_id,
            state='CHECKEDIN',
            creator=creator[:12], 
            owner='',
            data=''
        )
        
        bc.add_block(new_block)
        
        prev_hash = new_block.calculate_hash()
        
        print(f"Added item: {item_id_int}")
        print(f"Status: CHECKEDIN")
        print(f"Time of action: {datetime.utcfromtimestamp(timestamp).isoformat()}Z")
    
    return 0


def cmd_checkout(item_id, password):
    # any valid pasowrd works for checkout
    if not validate_password(password):
        print("Invalid password")
        return 1
    
    bc = Blockchain()
 
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    try:
        item_id_int = int(item_id)
    except ValueError:
        print("Error: Invalid item ID format.")
        return 1
    
    encrypted_item_id = encrypt_item_id(item_id_int)
       # item must already exist
    if not bc.item_exists(encrypted_item_id):
        print(f"Error: Item {item_id_int} not found in blockchain.")
        return 1
    
    current_state = bc.get_item_state(encrypted_item_id)
    # cannot remove or checkout invalid states
    if current_state in ['DISPOSED', 'DESTROYED', 'RELEASED']:
        print(f"Error: Cannot check out removed item.")
        return 1
    #pull item's block history
    if current_state == 'CHECKEDOUT':
        print(f"Error: Item is already checked out.")
        return 1

    item_blocks = bc.get_item_blocks(encrypted_item_id)
    case_id_encrypted = item_blocks[0].case_id
    
    original_creator = item_blocks[0].creator

    last_block = bc.get_last_block()
    prev_hash = last_block.calculate_hash()
    timestamp = datetime.utcnow().timestamp()

    owner_role = validate_password(password) # stores role as text
    #create CHECKEDOUT block
    new_block = Block(
        prev_hash=prev_hash,
        timestamp=timestamp,
        case_id=case_id_encrypted,
        evidence_id=encrypted_item_id,
        state='CHECKEDOUT',
        creator=original_creator,
        owner=owner_role,
        data=''
    )
    
    bc.add_block(new_block)
    
    case_uuid = decrypt_case_id(case_id_encrypted)
    
    print(f"Case: {str(case_uuid)}")
    print(f"Checked out item: {item_id_int}")
    print(f"Status: CHECKEDOUT")
    print(f"Time of action: {datetime.utcfromtimestamp(timestamp).isoformat()}Z")
    
    return 0


def cmd_checkin(item_id, password):
    # same password eules as checkout 
    if not validate_password(password):
        print("Invalid password")
        return 1
    
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    try:
        item_id_int = int(item_id)
    except ValueError:
        print("Error: Invalid item ID format.")
        return 1
    
    encrypted_item_id = encrypt_item_id(item_id_int)
    #ensure item is valid
    if not bc.item_exists(encrypted_item_id):
        print(f"Error: Item {item_id_int} not found in blockchain.")
        return 1

    current_state = bc.get_item_state(encrypted_item_id)
    #cannot check in removed or already checked-in items
    if current_state in ['DISPOSED', 'DESTROYED', 'RELEASED']:
        print(f"Error: Cannot check in removed item.")
        return 1

    if current_state == 'CHECKEDIN':
        print(f"Error: Item is already checked in.")
        return 1

    item_blocks = bc.get_item_blocks(encrypted_item_id)
    case_id_encrypted = item_blocks[0].case_id
 
    original_creator = item_blocks[0].creator

    last_block = bc.get_last_block()
    prev_hash = last_block.calculate_hash()
    timestamp = datetime.utcnow().timestamp()

    owner_role = validate_password(password)
    # create CHECKEDIN block
    new_block = Block(
        prev_hash=prev_hash,
        timestamp=timestamp,
        case_id=case_id_encrypted,
        evidence_id=encrypted_item_id,
        state='CHECKEDIN',
        creator=original_creator,
        owner=owner_role,
        data=''
    )
    
    bc.add_block(new_block)

    case_uuid = decrypt_case_id(case_id_encrypted)
    
    print(f"Case: {str(case_uuid)}")
    print(f"Checked in item: {item_id_int}")
    print(f"Status: CHECKEDIN")
    print(f"Time of action: {datetime.utcfromtimestamp(timestamp).isoformat()}Z")
    
    return 0


def cmd_show_cases(password=None):
    # lists all unique case IDs
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    cases = bc.get_all_cases()
    
    for case_encrypted in cases:

        case_uuid = decrypt_case_id(case_encrypted)
        print(str(case_uuid))
    
    return 0


def cmd_show_items(case_id, password=None):
    # shows all items associated with a case 
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        print("Error: Invalid case ID format.")
        return 1
    
    encrypted_case_id = encrypt_case_id(case_uuid)
    
    items = bc.get_items_for_case(encrypted_case_id)
    
    if not items:
        return 0
    
    for item_encrypted in items:
     
        item_id = decrypt_item_id(item_encrypted)
        print(item_id)
    
    return 0


def cmd_show_history(password=None, case_id=None, item_id=None, num_entries=None, reverse=False):
    # password required to view history
    if not password or not validate_password(password):
        print("Invalid password")
        return 1
    
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    blocks = bc.get_all_blocks()
    # filter by case if provided 
    if case_id:
        try:
            case_uuid = uuid.UUID(case_id)
            encrypted_case_id = encrypt_case_id(case_uuid)
            blocks = [b for b in blocks if b.case_id == encrypted_case_id]
        except ValueError:
            print("Error: Invalid case ID format.")
            return 1
    # filter by item if needed
    if item_id:
        try:
            item_id_int = int(item_id)
            encrypted_item_id = encrypt_item_id(item_id_int)
            blocks = [b for b in blocks if b.evidence_id == encrypted_item_id]
        except ValueError:
            print("Error: Invalid item ID format.")
            return 1
    # hide INITIAL unless reversed/history requested
    if num_entries is None and not reverse:
        blocks = [b for b in blocks if b.state != 'INITIAL']
    
    if reverse:
        blocks = blocks[::-1]
    
    if num_entries:
        blocks = blocks[:num_entries]
    # print each entry in readable format
    for i, block in enumerate(blocks):
        case_uuid = decrypt_case_id(block.case_id)
        item_id_dec = decrypt_item_id(block.evidence_id)
        print(f"> Case: {str(case_uuid)}")
        print(f"> Item: {item_id_dec}")
        print(f"> Action: {block.state}")

        dt = datetime.utcfromtimestamp(block.timestamp)
        timestamp_str = dt.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
        print(f"> Time: {timestamp_str}")
        

        if i < len(blocks) - 1:
            print()
    
    return 0


def cmd_remove(item_id, reason, password, owner=None):
    # item removal only allowed by creator level password
    if not is_creator_password(password):
        print("Invalid password")
        return 1
    
    valid_reasons = ['DISPOSED', 'DESTROYED', 'RELEASED']
    if reason not in valid_reasons:
        print(f"Error: Invalid reason. Must be one of: {', '.join(valid_reasons)}")
        return 1
    
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    try:
        item_id_int = int(item_id)
    except ValueError:
        print("Error: Invalid item ID format.")
        return 1
    
    encrypted_item_id = encrypt_item_id(item_id_int)
    # must already exist 
    if not bc.item_exists(encrypted_item_id):
        print(f"Error: Item {item_id_int} not found in blockchain.")
        return 1
    
    current_state = bc.get_item_state(encrypted_item_id)
    # only CHECKEDIN items can be removed 
    if current_state != 'CHECKEDIN':
        print(f"Error: Item must be in CHECKEDIN state to remove. Current state: {current_state}")
        return 1

    item_blocks = bc.get_item_blocks(encrypted_item_id)
    case_id_encrypted = item_blocks[0].case_id
  
    original_creator = item_blocks[0].creator

    last_owner = item_blocks[-1].owner

    last_block = bc.get_last_block()
    prev_hash = last_block.calculate_hash()
    timestamp = datetime.utcnow().timestamp()

    data = ''
    # create final removal block
    new_block = Block(
        prev_hash=prev_hash,
        timestamp=timestamp,
        case_id=case_id_encrypted,
        evidence_id=encrypted_item_id,
        state=reason,
        creator=original_creator,
        owner=last_owner,
        data=data
    )
    
    bc.add_block(new_block)
 
    case_uuid = decrypt_case_id(case_id_encrypted)
    
    print(f"Case: {str(case_uuid)}")
    print(f"Removed item: {item_id_int}")
    print(f"Status: {reason}")
    if owner:
        print(f"Owner info: {owner}")
    print(f"Time of action: {datetime.utcfromtimestamp(timestamp).isoformat()}Z")
    
    return 0


def cmd_verify():
    # checks entire chain integrity 
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain file not found.")
        return 1
    
    blocks = bc.get_all_blocks()
    num_transactions = len(blocks)
    
    is_valid, message, bad_block, parent_block = bc.verify_chain()
    
    print(f"Transactions in blockchain: {num_transactions}")
    
    if is_valid:
        print(f"State of blockchain: {message}")
        return 0
    else:
        print(f"State of blockchain: ERROR")
        # show more context for failures 
        if bad_block:
            print(f"Bad block: {bad_block.get_hash_hex()}")
            
            if parent_block:
                print(f"Parent block: {parent_block.get_hash_hex()}")
                if "same parent" in message:
                    print(message)
            elif "NOT FOUND" in message:
                print(f"Parent block: NOT FOUND")
            
            if "checksum" in message or "after removal" in message:
                print(message)
        
        return 1


def cmd_summary(case_id):
    # gives quick state counts for a case
    bc = Blockchain()
    
    if not bc.file_exists():
        print("Error: Blockchain not initialized.")
        return 1
    
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        print("Error: Invalid case ID format.")
        return 1
    
    encrypted_case_id = encrypt_case_id(case_uuid)
    
    case_blocks = bc.get_case_blocks(encrypted_case_id)
    # no evidence means empty summary 
    if not case_blocks:
        print(f"Case Summary for Case ID: {case_id}")
        print(f"Total Evidence Items: 0")
        print(f"Checked In: 0")
        print(f"Checked Out: 0")
        print(f"Disposed: 0")
        print(f"Destroyed: 0")
        print(f"Released: 0")
        return 0
    # track counts by state
    state_counts = {
        'CHECKEDIN': 0,
        'CHECKEDOUT': 0,
        'DISPOSED': 0,
        'DESTROYED': 0,
        'RELEASED': 0
    }
    
    item_ids = set()
    
    for block in case_blocks:
        item_ids.add(block.evidence_id)
        if block.state in state_counts:
            state_counts[block.state] += 1
    
    total_items = len(item_ids)
    
    print(f"Case Summary for Case ID: {case_id}")
    print(f"Total Evidence Items: {total_items}")
    print(f"Checked In: {state_counts['CHECKEDIN']}")
    print(f"Checked Out: {state_counts['CHECKEDOUT']}")
    print(f"Disposed: {state_counts['DISPOSED']}")
    print(f"Destroyed: {state_counts['DESTROYED']}")
    print(f"Released: {state_counts['RELEASED']}")
    
    return 0