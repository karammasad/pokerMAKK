"""doku: Everything: all teammate attacks (turn/river/flop-mix pressure, mixed opens, river calls) over the City engine, adaptive bluffs, thin value vs stations."""
from bots import city_core as core

PROFILE = {'pot_cut': 0.74, 'half_cut': 0.35, 'call_margin': 0.3, 'pre_open': 0.52, 'tb_turn': True, 'tb_river': True, 'tb_flop_mix': True, 'open_mix': True, 'river_call_margin': 0.28, 'bluff': 0.05, 'station_thin': True}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
