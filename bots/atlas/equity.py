"""Prefix-reusable Monte Carlo sampling with the official Omaha evaluator."""
import random

from bots.common.cards import canonical_state
from bots.common.equity import _seed
from evaluator import omaha_score


def estimate(obs, memory, samples):
    if memory.get('_atlas_eq_hand') != obs.hand_index:
        memory['_atlas_eq_hand'] = obs.hand_index
        memory['_atlas_eq'] = {}
    hole, board = canonical_state(tuple(obs.hole_cards), tuple(obs.board))
    cache = memory['_atlas_eq']
    key = (hole, board)
    if key not in cache:
        dead = set(hole) | set(board)
        unseen = [c for c in range(36) if c not in dead]
        cache[key] = [random.Random(_seed(hole, board)), unseen, [0],
                      omaha_score(hole, board) if len(board) == 5 else None]
    rng, unseen, cumulative, river_score = cache[key]
    missing = 5 - len(board)
    while len(cumulative) <= samples:
        draw = rng.sample(unseen, 5 + missing)
        full_board = board + tuple(draw[5:])
        ours = river_score if river_score is not None else omaha_score(hole, full_board)
        theirs = omaha_score(tuple(draw[:5]), full_board)
        cumulative.append(cumulative[-1] + (2 if ours > theirs else 1 if ours == theirs else 0))
    return cumulative[samples] / (2 * samples) if samples else 0.5
