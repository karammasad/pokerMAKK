"""Train an abstract CFR+ response table for equity/pot-odds decision buckets.

This offline trainer uses external sampling over coarse, one-street payoff
matrices. It is a practical warm start, not a full-game equilibrium solve.
"""
import argparse
import json
import random
from pathlib import Path

ACTIONS = ("fold", "call", "half", "pot")
STREETS = ("FLOP", "TURN", "RIVER")


def regret_matching(regret):
    pos = [max(0.0, r) for r in regret]
    total = sum(pos)
    return [x / total for x in pos] if total else [0.25] * 4


def payoff(equity, odds, row, col):
    """Approximate chips gained by row, with a symmetric zero-sum opponent."""
    invest = [0.0, odds, min(1.0, odds * 1.6 + 0.08), min(1.0, odds * 2.1 + 0.12)]
    if row == 0:
        return -0.04 if col == 0 else -odds
    if col == 0 and row >= 2:
        return 0.25 + 0.5 * equity
    call_cost = invest[row]
    opp_cost = invest[col]
    return equity * (1.0 + opp_cost) - (1.0 - equity) * call_cost


def solve(equity, odds, iterations, rng):
    regret = [0.0] * 4
    average = [0.0] * 4
    matrix = [[payoff(equity, odds, a, b) for b in range(4)] for a in range(4)]
    for _ in range(iterations):
        policy = regret_matching(regret)
        opp = rng.choices(range(4), weights=policy, k=1)[0]
        values = [matrix[a][opp] for a in range(4)]
        ev = sum(policy[a] * values[a] for a in range(4))
        for a in range(4):
            regret[a] = max(0.0, regret[a] + values[a] - ev)
            average[a] += policy[a]
    total = sum(average) or 1.0
    return [x / total for x in average]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--out", default=str(Path(__file__).parents[1] / "tables" / "strategy.json"))
    args = ap.parse_args()
    rng = random.Random(913)
    table = {}
    for street in STREETS:
        for ebin in range(10):
            equity = (ebin + 0.5) / 10
            for obin in range(5):
                odds = (obin + 0.5) / 5
                table[f"{street}:{ebin}:{obin}"] = solve(equity, odds, args.iterations, rng)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(table, separators=(",", ":")))
    print(f"trained {len(table)} abstraction states")

if __name__ == "__main__":
    main()
