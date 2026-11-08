"""rodri: The fortress: tight, low-variance value play, never bluffs, switches to M5 vs spew."""
from bots import city_core as core

PROFILE = {'pot_cut': 0.8, 'half_cut': 0.42, 'call_margin': 0.33, 'pre_slack': 0.06, 'bluff': 0.0}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
