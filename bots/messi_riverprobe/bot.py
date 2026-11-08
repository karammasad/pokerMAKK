"""V7 with an evidence-gated, cost-limited river probe.

The observed fold rate includes every tracked river bet, not only bluffs.
That selection bias means this is an empirical heuristic, not a safety proof.
"""
from bots.messi_v7 import bot as baseline
from game import Action, Street


def load():
    baseline.load()


def new_half(config, memory):
    baseline.new_half(config, memory)
    memory['_rp_trials'] = 0
    memory['_rp_folds'] = 0
    memory['_rp_pending'] = None


def choose_action(obs, memory):
    if memory.get('_rp_pending') == obs.hand_index:
        memory['_rp_trials'] += 1
        memory['_rp_pending'] = None
    action = baseline.choose_action(obs, memory)
    legal = obs.legal_actions
    if (obs.street == Street.RIVER and obs.to_call == 0 and action == Action.CHECK_CALL
            and Action.RAISE_HALF in legal and memory['_rp_trials'] >= 12
            and (memory['_rp_folds'] + 1) / (memory['_rp_trials'] + 2) >= 0.65
            and (obs.hand_index * 31 + sum(obs.hole_cards)) % 4 == 0
            and obs.raise_to[Action.RAISE_HALF] - obs.my_bet <= obs.pot * 0.6
            and baseline.attack.base.base.estimate_equity(obs, max_samples=8 if memory.get('_think_s', 0) >= 1.5 else 48) < 0.375):
        action = Action.RAISE_HALF
    if obs.street == Street.RIVER and obs.to_call == 0 and action in (Action.RAISE_HALF, Action.RAISE_POT):
        memory['_rp_pending'] = obs.hand_index
    return action


def on_hand_end(result, memory):
    if memory.get('_rp_pending') == result.hand_index:
        memory['_rp_trials'] += 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_rp_folds'] += 1
        memory['_rp_pending'] = None
    baseline.on_hand_end(result, memory)
