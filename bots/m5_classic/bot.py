"""Equity baseline with a selective river bluff after an opponent checks."""
from bots.m1_equity import bot as base
from game import Action, Street


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)


def choose_action(obs, memory):
    action = base.choose_action(obs, memory)
    if (obs.street != Street.PREFLOP and obs.to_call > 2
            and action == Action.CHECK_CALL and Action.FOLD in obs.legal_actions
            and base.estimate_equity(obs) < obs.to_call / (obs.pot + obs.to_call) + 0.20):
        return Action.FOLD
    if (obs.street == Street.RIVER and obs.to_call == 0
            and action == Action.CHECK_CALL and Action.RAISE_HALF in obs.legal_actions
            and any(not record.is_me and record.street == Street.RIVER
                    and record.action == Action.CHECK_CALL for record in obs.action_history)
            and base.estimate_equity(obs) <= 0.25):
        return Action.RAISE_HALF
    return action


def on_hand_end(result, memory):
    base.on_hand_end(result, memory)
