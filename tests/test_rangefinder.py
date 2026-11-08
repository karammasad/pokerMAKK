from types import SimpleNamespace

from bots.rangefinder import bot
from game import Action, AgentConfig, Street


def _obs(history=(), street=Street.FLOP):
    board_by_street = {
        Street.FLOP: (5, 6, 7),
        Street.TURN: (5, 6, 7, 8),
        Street.RIVER: (5, 6, 7, 8, 9),
    }
    return SimpleNamespace(
        street=street,
        action_history=tuple(history),
        hole_cards=(0, 1, 2, 3, 4),
        board=board_by_street[street],
    )


def test_profile_counts_actor_and_action_by_street():
    history = [
        SimpleNamespace(street=Street.PREFLOP, is_me=True, action=Action.RAISE_HALF),
        SimpleNamespace(street=Street.PREFLOP, is_me=False, action=Action.CHECK_CALL),
        SimpleNamespace(street=Street.FLOP, is_me=False, action=Action.RAISE_POT),
    ]
    profile = bot._profile(_obs(history))
    assert profile[0] == int(Street.FLOP)
    assert profile[2] == 1  # our preflop raise
    assert profile[3] == 1  # opponent preflop call
    assert profile[8] == 1  # opponent flop raise


def test_only_showdown_reveals_are_added_to_range_memory():
    memory = {}
    bot.new_half(AgentConfig(), memory)
    profile = (int(Street.RIVER),) + (0,) * 16
    memory["_m6_latest_profile"] = profile
    memory["_m6_profiles_seen"] = {int(Street.RIVER): profile}
    folded = SimpleNamespace(went_to_showdown=False, opp_hole=None)
    bot.on_hand_end(folded, memory)
    assert memory["_m6_range_examples"] == []

    shown = SimpleNamespace(went_to_showdown=True, opp_hole=(10, 11, 12, 13, 14), board=(5, 6, 7, 8, 9))
    bot.on_hand_end(shown, memory)
    assert memory["_m6_range_examples"] == [{"profile": profile, "hand": shown.opp_hole}]


def test_blockers_remove_incompatible_revealed_hands():
    obs = _obs()
    profile = bot._profile(obs)
    examples = [
        {"profile": profile, "hand": (8, 9, 10, 11, 12)},
        {"profile": profile, "hand": (0, 13, 14, 15, 16)},
    ]
    eligible = bot._eligible_examples(obs, profile, examples)
    assert [hand for hand, _ in eligible] == [(8, 9, 10, 11, 12)]


def test_range_estimate_requires_support_and_returns_bounded_equity():
    obs = _obs(street=Street.RIVER)
    profile = bot._profile(obs)
    memory = {"_m6_range_examples": []}
    assert bot._range_equity(obs, memory, profile) is None

    memory["_m6_range_examples"] = [
        {"profile": profile, "hand": hand}
        for hand in ((10, 11, 12, 13, 14), (15, 16, 17, 18, 19), (20, 21, 22, 23, 24), (25, 26, 27, 28, 29))
    ]
    estimate = bot._range_equity(obs, memory, profile)
    assert estimate is not None
    assert 0.0 <= estimate[0] <= 1.0
    assert estimate[1] >= 3.5
