"""Build a suit-canonical preflop equity table (offline, never during a match)."""
import argparse
import itertools
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluator import omaha_score, warmup


def canon(hand):
    best = None
    for perm in itertools.permutations(range(4)):
        key = tuple(sorted(((c >> 2), perm[c & 3]) for c in hand))
        if best is None or key < best:
            best = key
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=100)
    ap.add_argument("--limit", type=int, default=0, help="debug: stop after N canonical hands")
    ap.add_argument("--out", default=str(Path(__file__).parent / "tables" / "preflop.json"))
    args = ap.parse_args()
    warmup()
    hands = {}
    for hand in itertools.combinations(range(36), 5):
        key = canon(hand)
        hands.setdefault(key, hand)
    items = list(hands.items())
    if args.limit:
        items = items[:args.limit]
    rng = random.Random(2026)
    result = {}
    deck = set(range(36))
    for idx, (key, hand) in enumerate(items, 1):
        unseen = list(deck.difference(hand))
        wins = 0.0
        for _ in range(args.samples):
            cards = rng.sample(unseen, 15)
            opp, board = cards[:5], cards[5:10]
            a, b = omaha_score(hand, board), omaha_score(opp, board)
            wins += 1.0 if a > b else 0.5 if a == b else 0.0
        result[";".join(f"{r}{s}" for r, s in key)] = round(wins / args.samples, 5)
        if idx % 1000 == 0:
            print(f"{idx}/{len(items)}")
    Path(args.out).write_text(json.dumps(result, separators=(",", ":")))
    print(f"wrote {len(result)} hands to {args.out}")

if __name__ == "__main__":
    main()
