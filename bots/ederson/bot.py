"""ederson: Adaptive exploiter: reads fold rate; bluffs hard at folders, thins value and stops bluffing at stations."""
from bots import city_core as core

PROFILE = {'half_cut': 0.36, 'tb_turn': True, 'tb_flop_mix': True, 'bluff': 0.08, 'bluff_pot': False, 'station_thin': True, 'river_call_margin': 0.28, 'open_mix': True}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
