from types import SimpleNamespace

from game import Action, Street, AgentConfig
from league.run import match


def test_bluffs_river_when_checked_to_with_weak_equity(monkeypatch):
    from bots.kestrel import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    obs = SimpleNamespace(street=Street.RIVER, to_call=0, pot=8, hand_index=0,
                           legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    memory = {'_kt_trials': {}, '_kt_folds': {}, '_kt_pending': None}
    assert bot.choose_action(obs, memory) == Action.RAISE_HALF
    assert memory['_kt_pending'] == (0, Street.RIVER)


def test_stops_river_bluffing_once_opponent_stops_folding(monkeypatch):
    from bots.kestrel import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    obs = SimpleNamespace(street=Street.RIVER, to_call=0, pot=8, hand_index=0,
                           legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    memory = {'_kt_trials': {Street.RIVER: 20}, '_kt_folds': {Street.RIVER: 0}, '_kt_pending': None}
    assert bot.choose_action(obs, memory) == Action.CHECK_CALL


def test_does_not_bluff_when_talon_already_has_value(monkeypatch):
    from bots.kestrel import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.RAISE_HALF)
    obs = SimpleNamespace(street=Street.TURN, to_call=0, pot=8, hand_index=0,
                           legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    memory = {'_kt_trials': {}, '_kt_folds': {}, '_kt_pending': None}
    assert bot.choose_action(obs, memory) == Action.RAISE_HALF
    assert memory['_kt_pending'] is None


def test_never_bluffs_flop():
    from bots.kestrel import bot
    assert Street.FLOP not in bot.BLUFF_STREETS


def test_plays_a_short_fresh_match_with_zero_errors():
    bot = __import__('bots.kestrel.bot', fromlist=['bot'])
    row = match('kestrel', 'm5_challenger', 1, 150)
    assert row['errors'] == 0
    assert row['fallbacks'] == 0
    assert row['think_s'] < 8.0
