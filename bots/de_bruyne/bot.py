"""de_bruyne: Precision playmaker: heavy equity refinement, adaptive bluffing, calls down aggressors."""
from bots import city_core as core

PROFILE = {'base_samples': 32, 'refine_samples': 80, 'band': 0.07, 'call_margin': 0.28, 'bluff': 0.04, 'aggro_mode': 'calldown', 'aggro_rate': 0.4}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
