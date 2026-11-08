from types import SimpleNamespace

from bots.m8_bayes_types import bot
from game import Action, Street


def test_bayesian_posterior_identifies_aggressive_action_history():
    events = [(0, 1)] * 24
    belief = bot.posterior(events)

    assert belief["aggressive"] > 0.95
    assert sum(belief.values()) == 1.0


def test_recent_action_window_can_recover_from_a_behavior_shift():
    events = [(0, 1)] * 24 + [(0, 0)] * 64
    belief = bot.posterior(events)

    assert belief["station"] > belief["aggressive"]


def test_observer_uses_previous_public_raise_as_bet_context():
    memory = {"_m8_hand": 1, "_m8_seen": 0, "_m8_events": []}
    obs = SimpleNamespace(
        hand_index=1, is_button=True,
        action_history=(
            SimpleNamespace(is_me=True, street=Street.FLOP, action=Action.RAISE_HALF),
            SimpleNamespace(is_me=False, street=Street.FLOP, action=Action.FOLD),
        ),
    )

    bot._observe(obs, memory)
    bot._observe(obs, memory)

    assert memory["_m8_events"] == [(1, 0)]
