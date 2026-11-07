"""Generate equity-labeled structural features for offline model fitting."""
import argparse
import random
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from bots.common.cards import hand_features, FEATURE_NAMES
from evaluator import omaha_score, warmup



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=32)
    ap.add_argument("--out", default=str(Path(__file__).parent / "train_data.npz"))
    args = ap.parse_args()
    warmup()
    rng = random.Random(2026)
    deck = list(range(36))
    xs, ys = [], []
    for i in range(args.states):
        cards = rng.sample(deck, 15)
        hole, opp, full = tuple(cards[:5]), tuple(cards[5:10]), tuple(cards[10:15])
        nboard = (0, 3, 4, 5)[i % 4]
        board = full[:nboard]
        feat = hand_features(hole, board)
        # Estimate conditional showdown equity by completing this partial board.
        unseen = [c for c in deck if c not in hole and c not in board]
        missing = 5 - len(board)
        equity = 0.0
        for _ in range(args.samples):
            draw = rng.sample(unseen, 5 + missing)
            final_board = tuple(board) + tuple(draw[5:])
            a = omaha_score(hole, final_board)
            b = omaha_score(tuple(draw[:5]), final_board)
            equity += 1.0 if a > b else 0.5 if a == b else 0.0
        xs.append([feat[k] for k in FEATURE_NAMES])
        ys.append(equity / args.samples)
        if (i + 1) % 10000 == 0:
            print(f"{i + 1}/{args.states}")
    np.savez_compressed(args.out, x=np.asarray(xs, dtype=np.float32), y=np.asarray(ys, dtype=np.float32))

if __name__ == "__main__":
    main()
