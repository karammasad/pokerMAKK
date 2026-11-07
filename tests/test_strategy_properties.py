"""Metamorphic checks for suit symmetry and deterministic equity estimates."""
import itertools
import random

from bots.common.cards import canonical_suits
from bots.common.equity import equity_vs_random


def relabel(cards, permutation):
    return tuple((card & ~3) | permutation[card & 3] for card in cards)


def test_canonical_suits_are_invariant_under_all_suit_relabels():
    rng = random.Random(20261107)
    permutation = (2, 0, 3, 1)
    for _ in range(200):
        cards = tuple(rng.sample(range(36), 10))
        assert canonical_suits(cards) == canonical_suits(relabel(cards, permutation))


def test_equity_estimator_is_reproducible_bounded_and_suit_invariant():
    hole = (0, 5, 13, 22, 35)
    board = (2, 9, 18, 27, 32)
    value = equity_vs_random(hole, board, samples=64)
    assert 0.0 <= value <= 1.0
    assert equity_vs_random(hole, board, samples=64) == value
    perm = (1, 3, 0, 2)
    assert equity_vs_random(relabel(hole, perm), relabel(board, perm), samples=64) == value
