"""Regression vectors for the challenge's unusual Short Deck Omaha rules."""
import pytest

from evaluator import (
    FLUSH, FULL_HOUSE, STRAIGHT, THREE_OF_A_KIND,
    category_of, omaha_score, score_five,
)


def card(rank, suit):
    return (rank << 2) | suit


def test_short_deck_category_order():
    flush = [card(r, 0) for r in (0, 1, 3, 5, 8)]
    full_house = [card(8, 0), card(8, 1), card(8, 2), card(0, 0), card(0, 1)]
    trips = [card(8, 0), card(8, 1), card(8, 2), card(1, 0), card(2, 1)]
    straight = [card(r, s) for r, s in zip(range(5), (0, 1, 2, 3, 0))]
    assert category_of(score_five(flush)) == FLUSH
    assert category_of(score_five(full_house)) == FULL_HOUSE
    assert score_five(flush) > score_five(full_house)
    assert category_of(score_five(trips)) == THREE_OF_A_KIND
    assert category_of(score_five(straight)) == STRAIGHT
    assert score_five(trips) > score_five(straight)


def test_ace_six_to_nine_is_lowest_straight():
    wheel = [card(r, s) for r, s in zip((8, 0, 1, 2, 3), (0, 1, 2, 3, 0))]
    ten_high = [card(r, s) for r, s in zip((4, 5, 6, 7, 8), (0, 1, 2, 3, 0))]
    assert category_of(score_five(wheel)) == STRAIGHT
    assert category_of(score_five(ten_high)) == STRAIGHT
    assert score_five(wheel) < score_five(ten_high)


def test_omaha_uses_exactly_two_hole_and_three_board_cards():
    hole = [card(2, 0), card(3, 0), card(0, 1), card(1, 1), card(2, 2)]
    board = [card(r, 0) for r in (4, 5, 6, 7, 8)]
    # The board alone is an ace-high straight flush. Omaha can use only three
    # board cards, so the best valid hand is the queen-high 8-to-Q straight flush.
    assert score_five(board) > omaha_score(hole, board)
    expected = score_five([card(r, 0) for r in (2, 3, 4, 5, 6)])
    assert omaha_score(hole, board) == expected


def test_evaluator_rejects_wrong_card_counts():
    with pytest.raises(ValueError):
        omaha_score([0, 1, 2, 3], [4, 5, 6, 7, 8])
    with pytest.raises(ValueError):
        omaha_score([0, 1, 2, 3, 4], [5, 6, 7, 8])
    with pytest.raises(ValueError):
        score_five([0, 1, 2, 3, 3])
