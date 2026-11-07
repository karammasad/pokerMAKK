from types import SimpleNamespace

from bots.portfolio import FoldEquityBot
from game import Action, Street


def _action(is_me, action):
    return SimpleNamespace(is_me=is_me, action=action, street=Street.FLOP)


def test_bayesian_response_observation_is_incremental_and_idempotent():
    bot = FoldEquityBot()
    memory = {
        "_ev_hand": 4,
        "_ev_seen_actions": 0,
        "_ev_pending": {"street": "FLOP", "action": "RAISE_HALF"},
        "_ev_counts": {},
    }
    obs = SimpleNamespace(
        hand_index=4,
        action_history=(_action(True, Action.RAISE_HALF), _action(False, Action.CHECK_CALL)),
    )

    bot._observe(obs, memory)
    bot._observe(obs, memory)

    assert memory["_ev_counts"] == {"FLOP:RAISE_HALF": [0, 1, 0]}
    assert memory["_ev_pending"] is None
    assert memory["_ev_seen_actions"] == 2


def test_bayesian_response_posterior_uses_shrunk_prior():
    bot = FoldEquityBot()
    memory = {"_ev_counts": {"TURN:RAISE_POT": [3, 1, 0]}}
    obs = SimpleNamespace(
        street=Street.TURN,
        raises_this_street=0,
        opp_stack=100,
        opp_bet=0,
        raise_to={Action.RAISE_POT: 20},
    )

    probs = bot._response_probs(obs, Action.RAISE_POT, memory)

    assert probs == [5 / 12, 6 / 12, 1 / 12]


def test_hand_end_records_fold_when_pending_bet_wins_without_showdown():
    bot = FoldEquityBot()
    memory = {
        "_ev_pending": {"street": "RIVER", "action": "RAISE_HALF"},
        "_ev_counts": {},
    }
    result = SimpleNamespace(went_to_showdown=False, winner="me")

    bot.on_hand_end(result, memory)

    assert memory["_ev_counts"] == {"RIVER:RAISE_HALF": [1, 0, 0]}
    assert memory["_ev_pending"] is None
