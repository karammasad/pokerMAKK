from types import SimpleNamespace

from bots.m7_cherki import bot
from game import Action, Street

LEGAL = (Action.FOLD, Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT)


def _obs(**kw):
    base = dict(street=Street.FLOP, hole_cards=(0, 5, 10, 15, 20), board=(1, 6, 11),
                to_call=0, pot=12, is_button=False, hand_index=1,
                legal_actions=LEGAL, action_history=())
    base.update(kw)
    return SimpleNamespace(**base)


def _memory(actions=0, raises=0):
    memory = {}
    bot.new_half(SimpleNamespace(num_hands=1000), memory)
    memory["_cherki_opp_actions"] = actions
    memory["_cherki_opp_raises"] = raises
    return memory


def test_refines_only_near_threshold(monkeypatch):
    samples = []
    estimates = iter((0.38, 0.40))
    monkeypatch.setattr(bot, "equity_vs_random", lambda h, b, n: samples.append(n) or next(estimates))
    assert bot.choose_action(_obs(), _memory()) == Action.RAISE_HALF
    assert samples == [32, 64]


def test_keeps_cheap_estimate_far_from_threshold(monkeypatch):
    samples = []
    monkeypatch.setattr(bot, "equity_vs_random", lambda h, b, n: samples.append(n) or 0.10)
    assert bot.choose_action(_obs(), _memory()) == Action.CHECK_CALL
    assert samples == [32]


def test_switches_to_m5_only_against_sustained_aggression(monkeypatch):
    monkeypatch.setattr(bot.m5, "choose_action", lambda obs, memory: "m5")
    monkeypatch.setattr(bot, "equity_vs_random", lambda h, b, n: 0.10)
    assert bot.choose_action(_obs(), _memory(actions=100, raises=95)) == "m5"
    assert bot.choose_action(_obs(), _memory(actions=100, raises=35)) != "m5"
    assert bot.choose_action(_obs(), _memory(actions=5, raises=5)) != "m5"
