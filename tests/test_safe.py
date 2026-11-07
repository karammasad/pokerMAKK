from types import SimpleNamespace

from bots.common.safe import wrap
from game import Action


class BadBot:
    def __init__(self, action):
        self.action = action

    def choose_action(self, obs, memory):
        if isinstance(self.action, Exception):
            raise self.action
        return self.action


def obs():
    return SimpleNamespace(legal_actions=(Action.FOLD, Action.CHECK_CALL), to_call=5)


def test_safe_catches_exception_and_illegal_action():
    for bot in (BadBot(RuntimeError("bad")), BadBot(Action.RAISE_POT)):
        memory = {}
        wrapped = wrap(bot)
        wrapped.new_half(SimpleNamespace(time_bank_seconds=8), memory)
        assert wrapped.choose_action(obs(), memory) == Action.FOLD
        assert memory["_fallbacks"] == 1


def test_safe_catches_slow_action(monkeypatch):
    import bots.common.safe as safe
    ticks = iter([0.0, 6.1, 6.1, 6.1])
    monkeypatch.setattr(safe.timing.time, "perf_counter", lambda: next(ticks))
    memory = {}
    wrapped = wrap(BadBot(Action.CHECK_CALL))
    wrapped.new_half(SimpleNamespace(time_bank_seconds=8), memory)
    assert wrapped.choose_action(obs(), memory) == Action.FOLD
    assert memory["_fallbacks"] == 1
