"""grealish: BALLSY: overbet bluffs on any street, bluff-raises, floats, light 3-bets, slowplays; stop-loss at -80bb falls back to safe play."""
from bots import city_core as core

PROFILE = {'pot_cut': 0.66, 'half_cut': 0.3, 'call_margin': 0.26, 'pre_pot': 0.72, 'pre_open': 0.48, 'pre_raise': 0.56, 'pre_light': 0.15, 'pre_light_floor': 0.46, 'bluff': 0.2, 'bluff_eq_max': 0.32, 'bluff_pot': True, 'bluff_any_street': True, 'bluff_raise': 0.07, 'float': 0.15, 'slowplay': 0.3, 'stop_loss_bb': 80}


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)


def choose_action(obs, memory):
    return core.choose_action(PROFILE, obs, memory)


def on_hand_end(result, memory):
    core.on_hand_end(PROFILE, result, memory)
