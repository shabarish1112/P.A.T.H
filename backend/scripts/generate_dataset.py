from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

AGENCIES = ['Public Works', 'Health', 'Education', 'Water Resources', 'Rural Development']
SCHEMES = ['Road Renewal', 'Primary Health', 'School Upgrade', 'Water Supply', 'Rural Works']
DISTRICTS = ['Bengaluru Urban', 'Mysuru', 'Kalaburagi', 'Tumakuru', 'Dharwad']


def main() -> None:
    rng = random.Random(42)
    output = Path(__file__).resolve().parents[2] / 'data' / 'public_fund_demo.csv'
    output.parent.mkdir(parents=True, exist_ok=True)
    budgets = {scheme: rng.randint(120_000_000, 450_000_000) for scheme in SCHEMES}
    start = date(2024, 4, 1)
    rows = []
    for index in range(4000):
        scheme_index = rng.randrange(len(SCHEMES))
        scheme = SCHEMES[scheme_index]
        agency = AGENCIES[scheme_index]
        anomaly = index % 197 == 0
        amount = rng.randint(80_000, 1_200_000) * (8 if anomaly else 1)
        tx_date = start + timedelta(days=rng.randrange(0, 730))
        rows.append(
            {
                'transaction_id': f'TX-{index + 1:06d}',
                'date': tx_date.isoformat(),
                'agency': agency,
                'scheme': scheme,
                'vendor': f'Vendor-{rng.randrange(1, 240):03d}',
                'district': rng.choice(DISTRICTS),
                'amount': amount,
                'sanctioned_amount': budgets[scheme],
                'payment_type': 'Electronic',
                'reversal_flag': 'false',
                'cancelled_flag': 'false',
                'injected_anomaly': str(anomaly).lower(),
            }
        )
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} rows to {output}')


if __name__ == '__main__':
    main()
