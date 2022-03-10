import pandas as pd
from collections import defaultdict
from ethereum_stats import EthereumStats
import argparse
import datetime

parser = argparse.ArgumentParser(description='Compute percentages of NFT activity relative to all Ethereum activity.')
parser.add_argument('prefix', type=str, help='Input/output file prefix.')
args = parser.parse_args()

stats = EthereumStats()

today = str(datetime.datetime.now().date())

compiled = defaultdict(dict)
for kind, name, baseline in [('tx-count', 'Transactions', stats.tx_count),
                       ('gas', 'Gas', stats.gas_used),
                       ('fees', 'Fees', stats.tx_fees)]:
    data = pd.read_csv(f'output/{args.prefix}-{kind}.csv', index_col='Date')
    totals = data.values.sum(1)
    dates = [e.date() for e in pd.to_datetime(data.index)]
    for date, value in zip(dates, totals):
        compiled[date][name] = value / baseline[date]

    pct = data.divide([baseline[e] for e in dates], axis='index')
    pct = pct[pct.index != today]
    pct.to_csv(f'output/{args.prefix}-{kind}-percentages.csv')

df = pd.DataFrame(compiled).transpose()
df.index.name = 'Date'
df = df[df.index != today]
df.to_csv(f'output/{args.prefix}-percentages.csv')