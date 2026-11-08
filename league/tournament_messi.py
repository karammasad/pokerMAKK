"""Supplemental pairings for `messi` vs the existing 11-bot shortlist, same
pooled official-format method as league/tournament.py. Run after the main
round-robin so results.csv gets the missing messi-vs-X rows without
restarting the whole thing.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from league.tournament import SHORTLIST, DEALS, SEEDS, pooled_match

OPPONENTS = SHORTLIST  # the original 11


def main():
    out_csv = "league/results.csv"
    rows = []
    print(f"Running messi vs {len(OPPONENTS)} shortlist bots x {len(SEEDS)} seeds x {DEALS} deals...",
          flush=True)
    exists = os.path.exists(out_csv) and os.path.getsize(out_csv) > 0
    f = open(out_csv, "a", newline="")
    w = csv.DictWriter(f, fieldnames=["bot", "opponent", "seed", "deals", "bb_deal", "ci_low", "ci_high",
                                       "verdict", "errors", "fallbacks", "think_s", "p50_ms", "p99_ms", "elapsed"],
                        extrasaction="ignore")
    if not exists:
        w.writeheader()
    for i, opp in enumerate(OPPONENTS, 1):
        r = pooled_match("messi", opp)
        rows.append(r)
        row = dict(r)
        row["seed"] = "pooled:" + ",".join(str(s) for s in r["seeds"])
        row["deals"] = r["n_deals"]
        row["fallbacks"] = 0
        row["think_s"] = 0.0
        row["p50_ms"] = 0.0
        row["p99_ms"] = 0.0
        w.writerow(row)
        f.flush()
        print(f"[{i}/{len(OPPONENTS)}] messi vs {opp}: {r['verdict']} {r['bb_deal']:+.4f} bb/deal "
              f"CI[{r['ci_low']:+.4f},{r['ci_high']:+.4f}] n={r['n_deals']} errors={r['errors']} "
              f"elapsed={r['elapsed']:.1f}s", flush=True)
    f.close()
    print("messi pairings done.", flush=True)


if __name__ == "__main__":
    main()
