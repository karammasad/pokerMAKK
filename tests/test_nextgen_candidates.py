from types import SimpleNamespace

import pytest

from bots.telltide import bot as telltide_bot
from bots.riverloom import bot as riverloom_bot
from game import Action, Street


def test_telltide_fold_ev_returns_the_current_pot(monkeypatch):
    obs = SimpleNamespace(pot=10, my_bet=0, opp_bet=0, opp_stack=20,
                          raise_to={Action.RAISE_HALF: 4})
    ev = telltide_bot._bet_ev(obs, 0.0, Action.RAISE_HALF, (1.0, 0.0, 0.0))
    assert ev == 10


@pytest.mark.parametrize(
    "winner,showdown,expected",
    [("me", False, 0), ("opp", True, 1), ("opp", False, 1)],
)
def test_telltide_records_terminal_bet_responses(monkeypatch, winner, showdown, expected):
    monkeypatch.setattr(telltide_bot.base, "on_hand_end", lambda result, memory: None)
    memory = {"_telltide_pending": (int(Street.RIVER), Action.RAISE_HALF.name),
              "_telltide_responses": {}}
    result = SimpleNamespace(winner=winner, went_to_showdown=showdown)
    telltide_bot.on_hand_end(result, memory)
    assert memory["_telltide_responses"]["3:RAISE_HALF"][expected] == 1
    assert memory["_telltide_pending"] is None


def test_telltide_marks_base_raise_even_on_early_return():
    memory = {"_telltide_pending": None, "_telltide_seen_actions": 0}
    obs = SimpleNamespace(street=Street.RIVER, action_history=[])
    action = telltide_bot._finish_action(obs, memory, Action.RAISE_POT)
    assert action == Action.RAISE_POT
    assert memory["_telltide_pending"] == (int(Street.RIVER), Action.RAISE_POT.name)


def test_riverloom_uses_nested_sample_estimate_without_reweighting(monkeypatch):
    calls = []

    def estimate(hole, board, samples):
        calls.append(samples)
        return {16: 0.50, 32: 0.55, 64: 0.70}[samples]

    monkeypatch.setattr(riverloom_bot, "equity_vs_random", estimate)
    obs = SimpleNamespace(hole_cards=(0, 1, 2, 3, 4), board=(5, 6, 7, 8, 9),
                          street=Street.RIVER, to_call=2, pot=8)
    memory = {"_think_s": 0.0, "_riverloom_refines": 0}
    result = riverloom_bot._equity(obs, memory)
    assert calls == [16, 32, 64]
    assert result == 0.70
