"""Rook policy with cached postflop equity and the exact river sampler."""
from bots.m5_classic import bot as anchor
from bots.m1_team_tuned.equity import equity_vs_random
from game import Action, Street


def load():
    anchor.load()


def new_half(config, memory):
    anchor.new_half(config, memory)
    memory['_rook_fast_hand'] = None
    memory['_rook_fast_equity'] = {}


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        return anchor.choose_action(obs, memory)
    if memory.get('_rook_fast_hand') != obs.hand_index:
        memory['_rook_fast_hand'] = obs.hand_index
        memory['_rook_fast_equity'] = {}
    key = (tuple(obs.hole_cards), tuple(obs.board))
    cache = memory.setdefault('_rook_fast_equity', {})
    if key not in cache:
        cache[key] = equity_vs_random(*key, 48)
    equity = cache[key]
    legal = obs.legal_actions
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
    anchor.on_hand_end(result, memory)
