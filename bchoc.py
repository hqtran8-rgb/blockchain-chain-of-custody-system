#!/usr/bin/env python3

import sys
import argparse
from commands import (
    cmd_init, cmd_add, cmd_checkout, cmd_checkin,
    cmd_show_cases, cmd_show_items, cmd_show_history,
    cmd_remove, cmd_verify, cmd_summary
)

def main():
    # main CLI enctrypoint for interacting with the blockchain system
    parser = argparse.ArgumentParser(
        prog='bchoc',
        description='Blockchain Chain of Custody',
        add_help=True
    )
    # group of all supported commands 
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    # init command setup
    parser_init = subparsers.add_parser('init', help='Initialize blockchain')
    # add command options
    parser_add = subparsers.add_parser('add', help='Add evidence item')
    parser_add.add_argument('-c', '--case_id', required=True, help='Case UUID')
    parser_add.add_argument('-i', '--item_id', action='append', required=True, 
                           help='Item ID (can specify multiple)')
    parser_add.add_argument('-g', '--creator', required=True, help='Creator name')
    parser_add.add_argument('-p', '--password', required=True, help='Password')
    #checkout options
    parser_checkout = subparsers.add_parser('checkout', help='Check out evidence item')
    parser_checkout.add_argument('-i', '--item_id', required=True, help='Item ID')
    parser_checkout.add_argument('-p', '--password', required=True, help='Password')
    # checkin options
    parser_checkin = subparsers.add_parser('checkin', help='Check in evidence item')
    parser_checkin.add_argument('-i', '--item_id', required=True, help='Item ID')
    parser_checkin.add_argument('-p', '--password', required=True, help='Password')
    # show parent command 
    parser_show = subparsers.add_parser('show', help='Show information')
    show_subparsers = parser_show.add_subparsers(dest='show_command', help='What to show')
    # show cases 
    parser_show_cases = show_subparsers.add_parser('cases', help='Show all cases')
    parser_show_cases.add_argument('-p', '--password', required=False, help='Password')
    # show items for a case 
    parser_show_items = show_subparsers.add_parser('items', help='Show items for a case')
    parser_show_items.add_argument('-c', '--case_id', required=True, help='Case UUID')
    parser_show_items.add_argument('-p', '--password', required=False, help='Password')
    # show history options
    parser_show_history = show_subparsers.add_parser('history', help='Show blockchain history')
    parser_show_history.add_argument('-c', '--case_id', help='Filter by case ID')
    parser_show_history.add_argument('-i', '--item_id', help='Filter by item ID')
    parser_show_history.add_argument('-n', '--num_entries', type=int, help='Number of entries')
    parser_show_history.add_argument('-r', '--reverse', action='store_true', 
                                    help='Reverse order (newest first)')
    parser_show_history.add_argument('-p', '--password', required=False, help='Password')
    # remove command
    parser_remove = subparsers.add_parser('remove', help='Remove evidence item')
    parser_remove.add_argument('-i', '--item_id', required=True, help='Item ID')
    parser_remove.add_argument('-y', '--why', required=True, 
                              choices=['DISPOSED', 'DESTROYED', 'RELEASED'],
                              help='Reason for removal')
    parser_remove.add_argument('-p', '--password', required=True, help='Password')
    parser_remove.add_argument('-o', '--owner', help='Owner (required for RELEASED)')
    # verify chain integrity
    parser_verify = subparsers.add_parser('verify', help='Verify blockchain integrity')
    # case summary command 
    parser_summary = subparsers.add_parser('summary', help='Show case summary')
    parser_summary.add_argument('-c', '--case_id', required=True, help='Case UUID')
    # parse user input 
    args = parser.parse_args()

    exit_code = 0
    
    try:
        # dispatch to correct command handler 
        if args.command == 'init':
            exit_code = cmd_init()
        
        elif args.command == 'add':
            exit_code = cmd_add(args.case_id, args.item_id, args.creator, args.password)
        
        elif args.command == 'checkout':
            exit_code = cmd_checkout(args.item_id, args.password)
        
        elif args.command == 'checkin':
            exit_code = cmd_checkin(args.item_id, args.password)
        
        elif args.command == 'show':
            # nested show subcommands
            if args.show_command == 'cases':
                exit_code = cmd_show_cases(args.password)
            
            elif args.show_command == 'items':
                exit_code = cmd_show_items(args.case_id, args.password)
            
            elif args.show_command == 'history':
                exit_code = cmd_show_history(
                    args.password,
                    case_id=args.case_id,
                    item_id=args.item_id,
                    num_entries=args.num_entries,
                    reverse=args.reverse
                )
            else:
                parser_show.print_help()
                exit_code = 1
        
        elif args.command == 'remove':
            exit_code = cmd_remove(args.item_id, args.why, args.password, args.owner)
        
        elif args.command == 'verify':
            exit_code = cmd_verify()
        
        elif args.command == 'summary':
            exit_code = cmd_summary(args.case_id)
        
        else:
            parser.print_help()
            exit_code = 1
    
    except Exception as e:
        # catch unexpected runtime errors for safer CLI behavior
        print(f"Error: {str(e)}", file=sys.stderr)
        exit_code = 1
    # return exit status to shell 
    sys.exit(exit_code)


if __name__ == '__main__':
    main()