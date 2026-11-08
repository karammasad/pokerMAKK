"""stones: Disciplined pressure: gated turn pressure + river calls only, thin value vs stations, no extra bluffs."""
from bots import city_core as core

PROFILE = {'tb_turn': True, 'river_call_margin': 0.28, 'station_thin': True, 'bluff': 0.0}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
