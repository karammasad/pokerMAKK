from types import SimpleNamespace

from bots.m10_seq_cfr import bot
from bots.mccfr.core import info_key, info_key_sequence
from game import Action, Street


def test_sequence_key_keeps_action_order_that_compact_key_merges():
    first = SimpleNamespace(street=Street.FLOP, is_me=True, action=Action.RAISE_HALF,
                            amount=4, street_total=4)
    second = SimpleNamespace(street=Street.FLOP, is_me=False, action=Action.CHECK_CALL,
                             amount=4, street_total=4)
    compact_a = SimpleNamespace(street=Street.FLOP, to_call=0, pot=12, my_stack=70,
                                is_button=True, raises_this_street=1,
                                legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF),
                                action_history=(first, second), hole_cards=(0, 5, 10, 15, 20), board=(1, 6, 11))
    compact_b = SimpleNamespace(**{**vars(compact_a), "action_history": (second, first)})

    assert info_key(compact_a) == info_key(compact_b)
    assert info_key_sequence(compact_a) != info_key_sequence(compact_b)


def test_sequence_cfr_falls_back_on_unseen_state(monkeypatch):
    monkeypatch.setattr(bot, "_POLICY", {})
    monkeypatch.setattr(bot, "info_key_sequence", lambda obs: "unseen")
    monkeypatch.setattr(bot.fallback, "choose_action", lambda obs, memory: Action.CHECK_CALL)
    obs = SimpleNamespace(legal_actions=(Action.CHECK_CALL,))

    assert bot.choose_action(obs, {}) == Action.CHECK_CALL
