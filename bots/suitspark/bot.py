"""Suitspark: Omaha-specific, preflop-action-conditioned range equity.

It samples opponent holdings from the exact Short Deck PLO5 preflop table,
weights them toward/away from strong holdings according to observed preflop
aggression, then shrinks that estimate toward random-hand equity. The model is
deliberately weakly weighted because teammates' policies differ.
"""
import math
import random

from bots.common.cards import canonical_suits
from bots.common.equity import equity_vs_random
from bots.m5_counterplay import bot as base
from evaluator import omaha_score
from game import Action, Street


_RANGE_SAMPLES = 12
_CANDIDATE_HANDS = 48


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)


def _preflop_raise_seen(obs):
    return any(not r.is_me and r.street == Street.PREFLOP
               and r.action in (Action.RAISE_HALF, Action.RAISE_POT)
               for r in obs.action_history)


def _hand_strength(hand):
    key = ";".join(f"{rank}{suit}" for rank, suit in canonical_suits(hand))
    return float((base._PREFLOP or {}).get(key, 0.5))


def _action_likelihood(strength, raised):
    scaled = min(1.0, max(0.0, (strength - 0.32) / 0.50))
    return 0.12 + 0.76 * (scaled if raised else 1.0 - scaled)


def _conditioned_equity(obs):
    dead = set(obs.hole_cards) | set(obs.board)
    unseen = [card for card in range(36) if card not in dead]
    raised = _preflop_raise_seen(obs)
    rng = random.Random((obs.hand_index * 65537 + sum(obs.hole_cards) * 257
                         + sum(obs.board) * 17 + int(obs.street)) & 0xFFFFFFFF)
    hands, weights = [], []
    for _ in range(_CANDIDATE_HANDS):
        hand = tuple(rng.sample(unseen, 5))
        hands.append(hand)
        weights.append(_action_likelihood(_hand_strength(hand), raised))

    missing = 5 - len(obs.board)
    own_river = omaha_score(obs.hole_cards, obs.board) if missing == 0 else None
    score = 0.0
    for opponent in rng.choices(hands, weights=weights, k=_RANGE_SAMPLES):
        remaining = [card for card in unseen if card not in opponent]
        future = rng.sample(remaining, missing)
        board = tuple(obs.board) + tuple(future)
        ours = own_river if own_river is not None else omaha_score(obs.hole_cards, board)
        theirs = omaha_score(opponent, board)
        score += 1.0 if ours > theirs else 0.5 if ours == theirs else 0.0
    return score / _RANGE_SAMPLES


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        return base.choose_action(obs, memory)
    legal = obs.legal_actions
    prior = equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), 16)
    conditioned = _conditioned_equity(obs)
    # Cap influence to limit model error from unknown teammate policies.
    mix = 0.25
    equity = (1.0 - mix) * prior + mix * conditioned
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        if equity >= 0.90 and Action.RAISE_POT in legal:
            return Action.RAISE_POT
        if equity >= 0.90 and Action.RAISE_HALF in legal:
            return Action.RAISE_HALF
        if obs.to_call > 2 and equity < odds + 0.30 and Action.FOLD in legal:
            return Action.FOLD
        return Action.CHECK_CALL
    if equity >= 0.76 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if equity >= 0.375 and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def on_hand_end(result, memory):
    base.on_hand_end(result, memory)
