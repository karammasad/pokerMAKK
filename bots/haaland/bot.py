"""haaland: Relentless pressure: thin value bets, adaptive river bluffs, wide aggressive preflop."""
from bots import city_core as core

PROFILE = {'pot_cut': 0.7, 'half_cut': 0.33, 'call_margin': 0.3, 'pre_pot': 0.74, 'pre_open': 0.52, 'pre_raise': 0.6, 'bluff': 0.06, 'bluff_pot': False}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
