"""Guardrails shared by every strategy module."""
from bots.common import timing
from types import SimpleNamespace

from game import Action


def _fallback(obs):
    if Action.CHECK_CALL in obs.legal_actions and obs.to_call == 0:
        return Action.CHECK_CALL
    if Action.CHECK_CALL in obs.legal_actions and obs.to_call <= 2:
        return Action.CHECK_CALL
    if Action.FOLD in obs.legal_actions:
        return Action.FOLD
    return obs.legal_actions[0]


def wrap(module):
    def new_half(config, memory):
        memory.setdefault("_think_s", 0.0)
        memory.setdefault("_fallbacks", 0)
        memory["_half_budget"] = float(getattr(config, "time_bank_seconds", 8.0))
        try:
            hook = getattr(module, "new_half", None)
            if hook:
                hook(config, memory)
        except Exception:
            pass

    def choose_action(obs, memory):
        start = timing.start()
        try:
            action = module.choose_action(obs, memory)
            elapsed = timing.elapsed_ms(start) / 1000.0
            if action not in obs.legal_actions or memory.get("_think_s", 0.0) + elapsed > 6.0:
                action = _fallback(obs)
                memory["_fallbacks"] = memory.get("_fallbacks", 0) + 1
        except Exception:
            action = _fallback(obs)
            memory["_fallbacks"] = memory.get("_fallbacks", 0) + 1
        elapsed = timing.elapsed_ms(start) / 1000.0
        timing.record(memory, elapsed)
        return action

    def on_hand_end(result, memory):
        try:
            hook = getattr(module, "on_hand_end", None)
            if hook:
                hook(result, memory)
        except Exception:
            pass

    return SimpleNamespace(new_half=new_half, choose_action=choose_action, on_hand_end=on_hand_end)
