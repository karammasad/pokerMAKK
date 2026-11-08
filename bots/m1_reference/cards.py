"""Card canonicalization and rank/suit structure features for short deck."""
from collections import Counter
import itertools

FEATURE_NAMES = (
    tuple(f"hole_rank_{r}" for r in range(9))
    + tuple(f"hole_suit_{s}" for s in range(4))
    + tuple(f"board_rank_{r}" for r in range(9))
    + tuple(f"board_suit_{s}" for s in range(4))
    + tuple(f"hole_rank_suit_{r}_{s}" for r in range(9) for s in range(4))
    + tuple(f"board_rank_suit_{r}_{s}" for r in range(9) for s in range(4))
    + tuple(f"hole_board_rank_{r}_{b}" for r in range(9) for b in range(9))
    + tuple(f"hole_board_suit_{s}_{t}" for s in range(4) for t in range(4))
    + ("rank_sum", "rank_pairs", "suit_pairs", "connected", "board_size", "board_suit_max", "board_rank_distinct")
)


def canonical_suits(cards):
    """Return a suit-relabeling invariant rank/suit tuple."""
    best = None
    for perm in itertools.permutations(range(4)):
        key = tuple(sorted(((card >> 2), perm[card & 3]) for card in cards))
        if best is None or key < best:
            best = key
    return best


def canonical_state(hole, board):
    """Canonicalize suit labels while keeping the private/public card groups."""
    best = None
    for perm in itertools.permutations(range(4)):
        h = tuple(sorted(((card >> 2) << 2) | perm[card & 3] for card in hole))
        b = tuple(sorted(((card >> 2) << 2) | perm[card & 3] for card in board))
        candidate = (h, b)
        if best is None or candidate < best:
            best = candidate
    return best


def hand_features(hole, board=()):
    ranks = [c >> 2 for c in hole]
    suits = [c & 3 for c in hole]
    rc, sc = Counter(ranks), Counter(suits)
    brc = Counter(c >> 2 for c in board)
    bsc = Counter(c & 3 for c in board)
    hrcs = Counter((c >> 2, c & 3) for c in hole)
    brcs = Counter((c >> 2, c & 3) for c in board)
    sorted_ranks = sorted(rc)
    values = {}
    for r in range(9):
        values[f"hole_rank_{r}"] = rc.get(r, 0) / 5.0
        values[f"board_rank_{r}"] = brc.get(r, 0) / 5.0
    for suit in range(4):
        values[f"hole_suit_{suit}"] = sc.get(suit, 0) / 5.0
        values[f"board_suit_{suit}"] = bsc.get(suit, 0) / 5.0
    for r in range(9):
        for suit in range(4):
            values[f"hole_rank_suit_{r}_{suit}"] = hrcs.get((r, suit), 0) / 5.0
            values[f"board_rank_suit_{r}_{suit}"] = brcs.get((r, suit), 0) / 5.0
        for br in range(9):
            values[f"hole_board_rank_{r}_{br}"] = rc.get(r, 0) * brc.get(br, 0) / 25.0
    for hs in range(4):
        for bs in range(4):
            values[f"hole_board_suit_{hs}_{bs}"] = sc.get(hs, 0) * bsc.get(bs, 0) / 25.0
    values.update({
        "rank_sum": sum(ranks) / 40.0,
        "rank_pairs": sum(n * (n - 1) / 2 for n in rc.values()) / 10.0,
        "suit_pairs": sum(n * (n - 1) / 2 for n in sc.values()) / 10.0,
        "connected": sum(b - a <= 2 for a, b in zip(sorted_ranks, sorted_ranks[1:])) / 4.0,
        "board_size": len(board) / 5.0,
        "board_suit_max": max(bsc.values(), default=0) / 5.0,
        "board_rank_distinct": len(brc) / 5.0,
    })
    return values
