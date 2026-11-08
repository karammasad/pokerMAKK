"""M5 opening strategy with pressure-oriented postflop counterplay.

A candidate for empirical evaluation, not an equilibrium strategy.
"""
from bots.m5_classic import bot as anchor
from bots.m5_counterplay import bot as pressure
from game import Street


def load():
    anchor.load()
    pressure.load()


def new_half(config, memory):
    anchor.new_half(config, memory)


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        return anchor.choose_action(obs, memory)
    return pressure.choose_action(obs, memory)


def on_hand_end(result, memory):
    anchor.on_hand_end(result, memory)
