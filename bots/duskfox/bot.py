"""Opponent-aware counterplay strategy: duskfox."""
from bots.common import counter_strategies as strategy


def load():
    strategy.load()


def new_half(config, memory):
    strategy.new_half(config, memory)


def choose_action(obs, memory):
    return strategy.choose_action(obs, memory, 'duskfox')


def on_hand_end(result, memory):
    strategy.on_hand_end(result, memory)
