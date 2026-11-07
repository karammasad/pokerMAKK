"""Refine near-threshold preflop equities offline; write output only to /tmp."""
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from evaluator import omaha_score, warmup


def main():
    with (ROOT / "bots/m1_equity/tables/preflop.json").open() as source:
        table = json.load(source)
    rng = random.Random(672981)
    warmup()
    keys = [key for key, equity in table.items() if 0.53 <= equity <= 0.69]
    print("training", len(keys), "hands", flush=True)
    for index, key in enumerate(keys, 1):
        hole = tuple(int(card[0]) * 4 + int(card[1]) for card in key.split(";"))
        unseen = [card for card in range(36) if card not in hole]
        score = 0.0
        for _ in range(250):
            cards = rng.sample(unseen, 10)
            ours = omaha_score(hole, cards[5:])
            theirs = omaha_score(cards[:5], cards[5:])
            score += 1 if ours > theirs else 0.5 if ours == theirs else 0
        table[key] = round((table[key] * 100 + score) / 350, 6)
        if index % 1000 == 0:
            print(index, "/", len(keys), flush=True)
    with open("/tmp/m6_preflop.json", "w") as output:
        json.dump(table, output, separators=(",", ":"))
    print("complete", flush=True)


if __name__ == "__main__":
    main()
