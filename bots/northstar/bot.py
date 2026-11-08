"""Experimental Telltide with a gated, per-half large river-call model."""
from bots.telltide import bot as base
from game import Action, Street
from bots.common.equity import equity_vs_random

def load():
    base.load()

def new_half(config, memory):
    base.new_half(config, memory)
    memory['_ns_river_trials'] = 0
    memory['_ns_river_wins'] = 0.0
    memory['_ns_river_pending'] = None

def _explore(obs):
    # Private-card mixing makes the exploration schedule less predictable.
    value = (2166136261 ^ obs.hand_index) & 0xffffffff
    for card in obs.hole_cards:
        value = ((value ^ (card + 1)) * 16777619) & 0xffffffff
    return value % 5 == 0


def choose_action(obs, memory):
    if obs.street != Street.PREFLOP and obs.to_call > 0 and memory.get('_think_s', 0.0) >= 1.2:
        # Preserve Telltide's observation bookkeeping while limiting the
        # expensive M5 equity calculation after a large fraction of the bank.
        base._observe(obs, memory)
        equity = equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), 8)
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        if equity >= 0.90 and Action.RAISE_POT in obs.legal_actions:
            action = Action.RAISE_POT
        elif equity >= 0.90 and Action.RAISE_HALF in obs.legal_actions:
            action = Action.RAISE_HALF
        elif obs.to_call > 2 and equity < odds + 0.30 and Action.FOLD in obs.legal_actions:
            action = Action.FOLD
        else:
            action = Action.CHECK_CALL
        action = base._finish_action(obs, memory, action)
    else:
        action = base.choose_action(obs, memory)
    if (obs.street == Street.RIVER and obs.to_call > 2 and
            3 * obs.to_call > obs.pot and action == Action.CHECK_CALL and
            Action.FOLD in obs.legal_actions):
        trials = memory['_ns_river_trials']
        win_rate = (memory['_ns_river_wins'] + 2.0) / (trials + 4.0)
        # Keep a fifth of calls to detect changes in an opponent's strategy.
        if trials >= 12 and win_rate < 0.30 and not _explore(obs):
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
