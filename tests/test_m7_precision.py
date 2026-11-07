from types import SimpleNamespace

from bots.m7_precision import bot
from game import Action, Street


def test_refines_equity_only_near_a_decision_threshold(monkeypatch):
    samples = []
    estimates = iter((0.64, 0.66))

    def estimate(hole, board, count):
        samples.append(count)
        return next(estimates)

    monkeypatch.setattr(bot, "equity_vs_random", estimate)
    monkeypatch.setattr(bot.base, "_PARAMS", {"value_pot": 0.76, "value_half": 0.63,
                                                "margin": 0.04, "bluff_freq": 0.0})
    memory = {"_m7_decisions": 0, "_m7_refinements_96": 0}
    obs = SimpleNamespace(
        street=Street.FLOP, hole_cards=(0, 5, 10, 15, 20), board=(1, 6, 11),
        to_call=0, pot=12, is_button=False, hand_index=1,
        legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT),
        action_history=(),
    )

    action = bot.choose_action(obs, memory)

    assert samples == [32, 96]
    assert action == Action.RAISE_HALF
    assert memory["_m7_refinements_96"] == 1


def test_keeps_low_sample_estimate_when_far_from_threshold(monkeypatch):
    samples = []
    monkeypatch.setattr(bot, "equity_vs_random", lambda hole, board, count: samples.append(count) or 0.30)
    monkeypatch.setattr(bot.base, "_PARAMS", {"value_pot": 0.76, "value_half": 0.63,
                                                "margin": 0.04, "bluff_freq": 0.0})
    memory = {"_m7_decisions": 0, "_m7_refinements_96": 0}
    obs = SimpleNamespace(
        street=Street.FLOP, hole_cards=(0, 5, 10, 15, 20), board=(1, 6, 11),
        to_call=0, pot=12, is_button=False, hand_index=1,
        legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT),
        action_history=(),
    )

    assert bot.choose_action(obs, memory) == Action.CHECK_CALL
    assert samples == [32]
