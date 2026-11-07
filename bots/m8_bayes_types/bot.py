"""Bayesian opponent-type posterior with conservative M5 responses.

The behavioral abstraction is intentionally small and uses only public action
history. It is inspired by Bayes' Bluff, not a reproduction of that solver.
"""
import math

from bots.m5_challenger import bot as anchor
from game import Action, Street


TYPES = ("overfolder", "station", "aggressive", "balanced")
PRIORS = {"overfolder": 0.20, "station": 0.25, "aggressive": 0.20, "balanced": 0.35}
# Likelihoods are P(action category | latent style, decision context).
FACING_BET = {
    "overfolder": (0.62, 0.34, 0.04),  # fold, call, raise
    "station": (0.03, 0.91, 0.06),
    "aggressive": (0.07, 0.38, 0.55),
    "balanced": (0.18, 0.68, 0.14),
}
NO_BET = {
    "overfolder": (0.82, 0.18),  # check/call, raise
    "station": (0.92, 0.08),
    "aggressive": (0.50, 0.50),
    "balanced": (0.75, 0.25),
}
WINDOW = 64


def load():
    anchor.load()


def new_half(config, memory):
    anchor.new_half(config, memory)
    memory["_m8_hand"] = -1
    memory["_m8_seen"] = 0
    memory["_m8_events"] = []


def _event_for(history, index, record, obs):
    previous = history[index - 1] if index else None
    facing_bet = bool(previous and previous.is_me and previous.action in
                       (Action.RAISE_HALF, Action.RAISE_POT))
    # On the first preflop action, the button faces the posted big blind.
    if (index == 0 and record.street == Street.PREFLOP and not obs.is_button):
        facing_bet = True
    if facing_bet:
        category = (0 if record.action == Action.FOLD else
                    1 if record.action == Action.CHECK_CALL else 2)
        return (1, category)
    category = 1 if record.action in (Action.RAISE_HALF, Action.RAISE_POT) else 0
    return (0, category)


def _observe(obs, memory):
    if memory.get("_m8_hand") != obs.hand_index:
        memory["_m8_hand"] = obs.hand_index
        memory["_m8_seen"] = 0
    history = obs.action_history
    events = memory["_m8_events"]
    for index in range(memory.get("_m8_seen", 0), len(history)):
        record = history[index]
        if not record.is_me:
            events.append(_event_for(history, index, record, obs))
            if len(events) > WINDOW:
                del events[0]
    memory["_m8_seen"] = len(history)


def posterior(events):
    log_weights = {kind: math.log(PRIORS[kind]) for kind in TYPES}
    for facing, category in events[-WINDOW:]:
        for kind in TYPES:
            likelihood = FACING_BET[kind][category] if facing else NO_BET[kind][category]
            log_weights[kind] += math.log(max(0.01, likelihood))
    peak = max(log_weights.values())
    weights = {kind: math.exp(value - peak) for kind, value in log_weights.items()}
    total = sum(weights.values())
    return {kind: weight / total for kind, weight in weights.items()}


def choose_action(obs, memory):
    _observe(obs, memory)
    action = anchor.choose_action(obs, memory)
    events = memory["_m8_events"]
    if len(events) < 12:
        return action
    beliefs = posterior(events)

    if (action == Action.FOLD and obs.street != Street.PREFLOP
            and Action.CHECK_CALL in obs.legal_actions and obs.to_call
            and beliefs["aggressive"] >= 0.80):
        equity = anchor.base.estimate_equity(obs)
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        if equity >= odds + 0.10:
            return Action.CHECK_CALL

    if (action == Action.RAISE_HALF and obs.street == Street.RIVER
            and Action.CHECK_CALL in obs.legal_actions
            and beliefs["station"] >= 0.80
            and anchor.base.estimate_equity(obs) <= 0.25):
        checked_to = any(not record.is_me and record.street == Street.RIVER
                         and record.action == Action.CHECK_CALL for record in obs.action_history)
        if checked_to:
            return Action.CHECK_CALL
    return action


def on_hand_end(result, memory):
    anchor.on_hand_end(result, memory)
