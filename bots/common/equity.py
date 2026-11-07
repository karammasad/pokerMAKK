"""Deterministic, cached Monte Carlo equity estimates using the official evaluator."""
import random
from functools import lru_cache
from evaluator import omaha_score


def _seed(hole, board):
    value = 2166136261
    for card in (*hole, 37, *board):
        value = ((value ^ int(card)) * 16777619) & 0xFFFFFFFF
    return value


@lru_cache(maxsize=512)
def _cached(hole, board, samples):
    dead = set(hole) | set(board)
    unseen = [c for c in range(36) if c not in dead]
    missing = 5 - len(board)
    rng = random.Random(_seed(hole, board))
    score = 0.0
    for _ in range(samples):
        draw = rng.sample(unseen, 5 + missing)
        full_board = tuple(board) + tuple(draw[5:])
        a = omaha_score(hole, full_board)
        b = omaha_score(tuple(draw[:5]), full_board)
        score += 1.0 if a > b else 0.5 if a == b else 0.0
    return score / samples if samples else 0.5


def equity_vs_random(hole, board=(), samples=32):
    """Estimate showdown equity against a uniformly random legal hand."""
    return _cached(tuple(hole), tuple(board), samples)
