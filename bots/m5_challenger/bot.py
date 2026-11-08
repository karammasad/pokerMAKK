"""Opponent-aware counterplay strategy: m5_challenger."""
from bots.common import counter_strategies as strategy


def load():
    strategy.load()


def new_half(config, memory):
    strategy.new_half(config, memory)


def choose_action(obs, memory):
    return strategy.choose_action(obs, memory, 'm5_challenger')


def on_hand_end(result, memory):
    strategy.on_hand_end(result, memory)
