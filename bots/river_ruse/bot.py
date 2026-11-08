"""Sparring policy that pressures every legal checked-to river."""
from bots.m5_counterplay import bot as base
from game import Action, Street

def load(): base.load()
def new_half(config, memory): base.new_half(config, memory)
def choose_action(obs, memory):
    if obs.street == Street.RIVER and obs.to_call == 0 and Action.RAISE_POT in obs.legal_actions:
        return Action.RAISE_POT
    return base.choose_action(obs, memory)
def on_hand_end(result, memory): base.on_hand_end(result, memory)
