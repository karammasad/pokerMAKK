from types import SimpleNamespace

from bots.m9_cfrplus import bot
from game import Action


def test_uses_trained_action_distribution(monkeypatch):
    action = Action.RAISE_HALF
    monkeypatch.setattr(bot, "MIN_VISITS", 0)
    monkeypatch.setattr(bot, "_POLICY", {"state": {"p": [0.0, 0.0, 1.0, 0.0]}})
    monkeypatch.setattr(bot, "info_key", lambda obs: "state")
    obs = SimpleNamespace(legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    memory = {"_m9_rng": __import__("random").Random(1)}

    assert bot.choose_action(obs, memory) == action


def test_falls_back_to_m5_for_unseen_information_set(monkeypatch):
    monkeypatch.setattr(bot, "_POLICY", {})
    monkeypatch.setattr(bot, "info_key", lambda obs: "unseen")
    monkeypatch.setattr(bot.fallback, "choose_action", lambda obs, memory: Action.CHECK_CALL)
    obs = SimpleNamespace(legal_actions=(Action.CHECK_CALL,))

    assert bot.choose_action(obs, {}) == Action.CHECK_CALL


def test_falls_back_when_cfr_information_set_is_undertrained(monkeypatch):
    monkeypatch.setattr(bot, "MIN_VISITS", 20)
    monkeypatch.setattr(bot, "_POLICY", {"state": {"p": [0.0, 0.0, 1.0, 0.0], "visits": 3}})
    monkeypatch.setattr(bot, "info_key", lambda obs: "state")
    monkeypatch.setattr(bot.fallback, "choose_action", lambda obs, memory: Action.CHECK_CALL)
    obs = SimpleNamespace(legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))

    assert bot.choose_action(obs, {}) == Action.CHECK_CALL
