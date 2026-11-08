from types import SimpleNamespace

from bots.m6_safeadapt import bot
from game import Action, Street


def _obs(**updates):
    values = dict(
        hand_index=0, street=Street.FLOP, hole_cards=(0, 5, 10, 15, 20), board=(1, 6, 11),
        to_call=4, pot=20, my_bet=0, opp_bet=4, my_stack=76, opp_stack=76,
        is_button=True, legal_actions=(Action.FOLD, Action.CHECK_CALL),
        raise_to={}, action_history=(),
    )
    values.update(updates)
    return SimpleNamespace(**values)


def _memory():
    return {
        "_m6_hand": 0, "_m6_seen": 0, "_m6_pending_bluff": True,
        "_m6_river_half_response": [0, 0], "_m6_raises": 0,
        "_m6_opp_actions": 0, "_m6_changes": 0, "_m6_change_budget": 50,
    }


def test_response_tracker_updates_once_from_public_history():
    memory = _memory()
    obs = _obs(street=Street.RIVER, action_history=(
        SimpleNamespace(is_me=False, street=Street.RIVER, action=Action.FOLD, amount=0),
    ))

    bot._observe(obs, memory)
    bot._observe(obs, memory)

    assert memory["_m6_river_half_response"] == [1, 0]
    assert memory["_m6_pending_bluff"] is False
    assert memory["_m6_opp_actions"] == 1


def test_adaptation_calls_wider_only_after_supported_aggression(monkeypatch):
    monkeypatch.setattr(bot.anchor, "choose_action", lambda obs, memory: Action.FOLD)
    monkeypatch.setattr(bot.anchor.base, "estimate_equity", lambda obs: 0.36)
    memory = _memory()
    memory["_m6_opp_actions"] = 60
    memory["_m6_raises"] = 45

    action = bot.choose_action(_obs(), memory)

    assert action == Action.CHECK_CALL


def test_river_bluff_is_suppressed_when_posterior_says_calls_are_likely(monkeypatch):
    monkeypatch.setattr(bot.anchor, "choose_action", lambda obs, memory: Action.RAISE_HALF)
    monkeypatch.setattr(bot.anchor.base, "estimate_equity", lambda obs: 0.10)
    memory = _memory()
    memory["_m6_pending_bluff"] = False
    memory["_m6_river_half_response"] = [0, 20]
    obs = _obs(
        street=Street.RIVER, to_call=0, pot=12, my_bet=0, opp_bet=0, opp_stack=80,
        action_history=(SimpleNamespace(is_me=False, street=Street.RIVER,
                                        action=Action.CHECK_CALL, amount=0),),
        legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT),
        raise_to={Action.RAISE_HALF: 6, Action.RAISE_POT: 12},
    )

    action = bot.choose_action(obs, memory)

    assert action == Action.CHECK_CALL
    assert memory["_m6_changes"] == 1
