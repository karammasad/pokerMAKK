"""Riverloom: sequential equity sampling near consequential thresholds."""
import math

from bots.common.equity import equity_vs_random
from bots.m5_counterplay import bot as base
from game import Action, Street


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory["_riverloom_refines"] = 0


def _thresholds(obs):
    if obs.to_call:
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        return (0.90, odds + 0.30)
    return (0.76, 0.375)


def _equity(obs, memory):
    hole, board = tuple(obs.hole_cards), tuple(obs.board)
    estimate = equity_vs_random(hole, board, 16)
    if obs.street == Street.PREFLOP:
        return estimate

    thresholds = _thresholds(obs)
    se = math.sqrt(max(0.0, estimate * (1.0 - estimate)) / 16.0)
    if min(abs(estimate - t) for t in thresholds) > 1.25 * se:
        return estimate
    if memory.get("_think_s", 0.0) >= 2.1:
        return estimate

    # equity_vs_random restarts its deterministic stream at sample zero for
    # every requested count, so larger estimates already include the smaller
    # prefixes. Use the larger estimate directly; averaging both would count
    # early samples multiple times and understate uncertainty.
    estimate = equity_vs_random(hole, board, 32)
    memory["_riverloom_refines"] += 1
    se = math.sqrt(max(0.0, estimate * (1.0 - estimate)) / 32.0)
    if min(abs(estimate - t) for t in thresholds) <= 1.1 * se:
        if memory.get("_think_s", 0.0) < 2.8:
            estimate = equity_vs_random(hole, board, 64)
            memory["_riverloom_refines"] += 1
    return estimate


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        return base.choose_action(obs, memory)
    equity = _equity(obs, memory)
    legal = obs.legal_actions
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        if equity >= 0.90 and Action.RAISE_POT in legal:
            return Action.RAISE_POT
        if equity >= 0.90 and Action.RAISE_HALF in legal:
            return Action.RAISE_HALF
        if obs.to_call > 2 and equity < odds + 0.30 and Action.FOLD in legal:
            return Action.FOLD
        return Action.CHECK_CALL
    if equity >= 0.76 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if equity >= 0.375 and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def on_hand_end(result, memory):
    base.on_hand_end(result, memory)
