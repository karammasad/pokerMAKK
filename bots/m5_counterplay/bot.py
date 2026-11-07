"""Postflop pressure and higher-sample equity against selective opponents."""
import json
from pathlib import Path
from bots.common.cards import canonical_suits
from bots.m1_equity import bot as base
from game import Action, Street


_PREFLOP = None


def load():
    global _PREFLOP
    base.load()
    try:
        _PREFLOP = json.loads((Path(__file__).parent / "preflop.json").read_text())
    except (OSError, ValueError):
        _PREFLOP = None


def new_half(config, memory):
    base.new_half(config, memory)


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
        equity = _PREFLOP.get(key) if _PREFLOP else None
        if equity is None:
            return base.choose_action(obs, memory)
        offset = 0.02 if obs.is_button else 0.0
        if equity >= 0.76 - offset and Action.RAISE_POT in obs.legal_actions:
            return Action.RAISE_POT
        opening = obs.is_button and obs.raises_this_street == 0
        if equity >= (0.56 if opening else 0.63 - offset) and Action.RAISE_HALF in obs.legal_actions:
            return Action.RAISE_HALF
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        if obs.to_call and equity < odds + 0.04 and Action.FOLD in obs.legal_actions:
            return Action.FOLD
        return Action.CHECK_CALL
    equity = base.estimate_equity(obs, max_samples=48)
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
