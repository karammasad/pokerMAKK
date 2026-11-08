"""V7 with a conservative showdown-conditioned range override for marginal calls.

The v7 action policy remains the default. Only a postflop fold facing a bet
may become a call, and only when several similar showdown hands support it.
"""
from bots.messi_v7 import bot as baseline
from bots.rangefinder import bot as range_model
from bots.common.equity import equity_vs_random
from game import Action, Street


def load():
    baseline.load()


def new_half(config, memory):
    baseline.new_half(config, memory)
    memory['_m6_range_examples'] = []
    memory['_m6_seen_hand'] = None
    memory['_m6_latest_profile'] = None
    memory['_m6_profiles_seen'] = {}
    memory['_m6_equity_cache'] = {}


def choose_action(obs, memory):
    if memory.get('_m6_seen_hand') != obs.hand_index:
        memory['_m6_seen_hand'] = obs.hand_index
        memory['_m6_latest_profile'] = None
        memory['_m6_profiles_seen'] = {}
        memory['_m6_equity_cache'].clear()
    profile = range_model._profile(obs)
    memory['_m6_latest_profile'] = profile
    memory['_m6_profiles_seen'][int(obs.street)] = profile
    action = baseline.choose_action(obs, memory)
    if (action != Action.FOLD or obs.street == Street.PREFLOP
            or Action.CHECK_CALL not in obs.legal_actions):
        return action
    estimate = range_model._range_equity(obs, memory, profile)
    if estimate is None:
        return action
    range_eq, effective_n = estimate
    if effective_n < 5.0:
        return action
    prior = equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), 16)
    mix = effective_n / (effective_n + range_model._PRIOR_STRENGTH)
    equity = (1.0 - mix) * prior + mix * range_eq
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    margin = {Street.FLOP: 0.12, Street.TURN: 0.10, Street.RIVER: 0.08}[obs.street]
    if equity >= odds + margin:
        return Action.CHECK_CALL
    return action


def on_hand_end(result, memory):
    range_model.on_hand_end(result, memory)
    baseline.on_hand_end(result, memory)
