"""Compare Method 1 parameter combinations on paired league seeds."""
import argparse
import csv
import itertools
import json
from pathlib import Path
from league.run import match

GRID = {
    "value_pot": (0.70, 0.75, 0.80),
    "value_half": (0.55, 0.60, 0.65),
    "margin": (0.0, 0.03, 0.06),
    "bluff_freq": (0.0, 0.05, 0.10),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opponent", default="random")
    ap.add_argument("--deals", type=int, default=100)
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--out", default="/tmp/m1-grid.csv")
    args = ap.parse_args()
    params_path = Path(__file__).with_name("params.json")
    original = json.loads(params_path.read_text())
    rows = []
    try:
        combos = itertools.product(*(GRID[k] for k in GRID))
        for values in combos:
            params = dict(zip(GRID, values))
            params_path.write_text(json.dumps(params))
            for seed in range(args.seeds):
                rows.append({**params, **match("m1_equity", args.opponent, seed, args.deals)})
    finally:
        params_path.write_text(json.dumps(original, indent=2) + "\n")
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f"wrote {len(rows)} candidate runs to {args.out}")

if __name__ == "__main__":
    main()
