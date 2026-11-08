"""gundogan: the captain - akanji's precision pressure with hybrid aggression handling (call down moderate aggressors, M5 style only vs true maniacs)."""
from bots import city_core as core

PROFILE = {'rr_cut': 0.85, 'no_refine_s': 1.3, 'panic_s': 2.1, 'panic_samples': 10, 'refine_samples': 80, 'band': 0.06, 'call_margin': 0.29, 'tb_turn': True, 'tb_river': True, 'open_mix': True, 'river_call_margin': 0.28, 'aggro_mode': 'hybrid', 'aggro_rate': 0.4, 'bluff': 0.03}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
