"""PSRO-lite payoff analysis over measured bots and zoo opponents."""
import argparse
import csv
from pathlib import Path

DEFAULT_BOTS = ("m1_equity", "m2_cfr", "m3_exploit", "m4_learned")


def replicator(payoffs, rounds=500):
    """Compute a simple population mixture with discrete replicator dynamics."""
    n = len(payoffs)
    if not n:
        return []
    mix = [1.0 / n] * n
    for _ in range(rounds):
        utility = [sum(mix[j] * payoffs[i][j] for j in range(n)) for i in range(n)]
        average = sum(mix[i] * utility[i] for i in range(n))
        mix = [mix[i] * max(0.0, 1.0 + 0.04 * (utility[i] - average)) for i in range(n)]
        total = sum(mix) or 1.0
        mix = [x / total for x in mix]
    return mix


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default="league/results.csv")
    ap.add_argument("--bots", default=",".join(DEFAULT_BOTS))
    args = ap.parse_args()
    bot_names = [x.strip() for x in args.bots.split(",") if x.strip()]
    sums, counts = {}, {}
    with Path(args.results).open(newline="") as f:
        for row in csv.DictReader(f):
            if row.get("bot") not in bot_names or not row.get("opponent"):
                continue
            try:
                value = float(row["bb_deal"])
            except (KeyError, ValueError):
                continue
            key = (row["bot"], row["opponent"])
            sums[key] = sums.get(key, 0.0) + value
            counts[key] = counts.get(key, 0) + 1
    opponents = sorted({opp for _, opp in sums})
    if not opponents:
        raise SystemExit("No matching league results found; run league/run.py first.")
    matrix = []
    for name in bot_names:
        row = [sums.get((name, opp), 0.0) / counts[(name, opp)] if (name, opp) in counts else 0.0 for opp in opponents]
        matrix.append(row)
    # Normalize each candidate to points against the measured zoo results.
    scores = [sum(row) / max(1, sum(1 for opp in opponents if any((name, opp) in counts for name in bot_names))) for row in matrix]
    mean = sum(scores) / len(scores) if scores else 0.0
    pairwise = [[scores[i] - scores[j] for j in range(len(scores))] for i in range(len(scores))]
    mix = replicator(pairwise)
    print("candidate,mean_bb_deal,mixture_weight")
    for name, score, weight in sorted(zip(bot_names, scores, mix), key=lambda x: x[1], reverse=True):
        print(f"{name},{score:+.4f},{weight:.3f}")

if __name__ == "__main__":
    main()
