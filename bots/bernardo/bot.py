"""bernardo: Trapper: slowplays monsters, sets check-raise traps, calls wider vs aggression."""
from bots import city_core as core

PROFILE = {'call_margin': 0.28, 'reraise_cut': 0.85, 'slowplay': 0.6, 'bluff': 0.03, 'aggro_mode': 'calldown', 'aggro_rate': 0.42, 'float': 0.1}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
