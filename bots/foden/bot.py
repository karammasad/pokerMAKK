"""foden: Balanced mix: moderate bluffs, occasional slowplays, M5 switch vs aggression."""
from bots import city_core as core

PROFILE = {'pot_cut': 0.74, 'half_cut': 0.36, 'call_margin': 0.3, 'bluff': 0.08, 'slowplay': 0.35, 'float': 0.08}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
