import argparse
from collections import defaultdict
import pandas as pd

from etherscan import Etherscan
from utils import load_contracts, load_etherscan_api_key, split_name_kind, get_timestamp

parser = argparse.ArgumentParser(description='Calculate total gas used and transaction fees paid by Ethereum platforms.')
parser.add_argument('contracts', nargs='+', help='List of contract JSON filenames')
parser.add_argument('--prefix', type=str, default=get_timestamp(), help='Output file prefix. Default: date and time.')
parser.add_argument('--noupdate', action='store_false', help='Do not update cache.')
parser.add_argument('--nosave', action='store_true', help='Do not save output.')
parser.add_argument('--update_active', type=int, default=None, help='Only update contracts that have had transactions in the last N days.')
parser.add_argument('--verbose', action='store_true', help='Verbose mode.')
args = parser.parse_args()

api_key = load_etherscan_api_key()
contracts = load_contracts(args.contracts)
etherscan = Etherscan(api_key)

gas_data = defaultdict(lambda:defaultdict(int))
fee_data = defaultdict(lambda:defaultdict(int))
tx_count_data = defaultdict(lambda:defaultdict(int))

global_gas_fees = 0
global_gas_used = 0
global_tx_count = 0

def print_stats(tx_count, gas_used, gas_fees):
    print(f'\ttransactions {tx_count:,}')
    print(f'\tgas_used {gas_used:,}')
    print(f'\tgas_fees {gas_fees/1e18:,.2f} ETH ({gas_fees})')

for name_kind, address in contracts.items():

    if args.verbose:
        print(name_kind)

    transactions = etherscan.load_transactions(address,
        update=args.noupdate,
        update_active=args.update_active,
        verbose=args.verbose)
        
    name, kind = split_name_kind(name_kind)

    all_gas_fees = 0
    all_gas_used = 0
    total_transactions = 0
    for tx in transactions:
        date = tx.get_datetime().date()
        gas_used = tx.gas_used
        gas_data[name][date] += gas_used
        all_gas_used += gas_used
        gas_fees = tx.get_fees()
        fee_data[name][date] += gas_fees
        all_gas_fees += gas_fees
        tx_count_data[name][date] += 1
        total_transactions += 1

    global_gas_fees += all_gas_fees
    global_gas_used += all_gas_used
    global_tx_count += total_transactions
    
    if args.verbose:
        print_stats(total_transactions, all_gas_used, all_gas_fees)

if args.verbose:
    print('Totals across all contracts:')
    print_stats(global_tx_count, global_gas_used, global_gas_fees)

def save_csv(data, fn, kind, scaling=None):
    if args.verbose:
        print(f'Writing to {fn}')
    df = pd.DataFrame(data)
    df.index.name = 'Date'
    df = df.sort_values('Date', ascending=True)
    df = df.fillna(0)
    if scaling is not None:
        df *= scaling
    df = df.astype(kind)
    df.to_csv(fn)

if not args.nosave:
    prefix = args.prefix
    save_csv(fee_data, f'output/{prefix}-fees.csv', float, 1/1e18)
    save_csv(gas_data, f'output/{prefix}-gas.csv', int)
    save_csv(tx_count_data, f'output/{prefix}-tx-count.csv', int)