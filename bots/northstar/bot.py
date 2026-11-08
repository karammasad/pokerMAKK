"""Experimental Telltide with a gated, per-half large river-call model."""
from bots.telltide import bot as base
from game import Action, Street

def load():
    base.load()

def new_half(config, memory):
    base.new_half(config, memory)
    memory['_ns_river_trials'] = 0
    memory['_ns_river_wins'] = 0.0
    memory['_ns_river_pending'] = None

def choose_action(obs, memory):
    action = base.choose_action(obs, memory)
    if (obs.street == Street.RIVER and obs.to_call > 2 and
            3 * obs.to_call > obs.pot and action == Action.CHECK_CALL and
            Action.FOLD in obs.legal_actions):
        trials = memory['_ns_river_trials']
        win_rate = (memory['_ns_river_wins'] + 2.0) / (trials + 4.0)
        # Keep a fifth of calls to detect changes in an opponent's strategy.
        if trials >= 12 and win_rate < 0.30 and obs.hand_index % 5 != 0:
            return Action.FOLD
        memory['_ns_river_pending'] = obs.hand_index
    return action

def on_hand_end(result, memory):
    if memory.get('_ns_river_pending') == result.hand_index:
        if result.went_to_showdown:
            memory['_ns_river_trials'] += 1
            memory['_ns_river_wins'] += 1.0 if result.winner == 'me' else 0.5 if result.winner == 'split' else 0.0
        memory['_ns_river_pending'] = None
    base.on_hand_end(result, memory)
