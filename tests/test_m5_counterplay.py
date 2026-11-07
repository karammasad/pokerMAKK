from types import SimpleNamespace
from game import Action, Street


def test_bets_marginal_flop_hand_when_checked_to(monkeypatch):
    from bots.m5_counterplay import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs, **kwargs: 0.40)
    obs = SimpleNamespace(street=Street.FLOP, to_call=0, pot=8, raises_this_street=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    assert bot.choose_action(obs, {}) == Action.RAISE_HALF


def test_folds_marginal_hand_to_postflop_pressure(monkeypatch):
    from bots.m5_counterplay import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs, **kwargs: 0.40)
    obs = SimpleNamespace(street=Street.FLOP, to_call=10, pot=30,
                          legal_actions=(Action.FOLD, Action.CHECK_CALL))
    assert bot.choose_action(obs, {}) == Action.FOLD


def test_avoids_thin_raise_into_postflop_bet(monkeypatch):
    from bots.m5_counterplay import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.RAISE_HALF)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs, **kwargs: 0.65)
    obs = SimpleNamespace(street=Street.FLOP, to_call=10, pot=30,
                          legal_actions=(Action.FOLD, Action.CHECK_CALL, Action.RAISE_HALF))
    assert bot.choose_action(obs, {}) == Action.CHECK_CALL


def test_checks_weak_flop_hand_without_a_reliable_draw(monkeypatch):
    from bots.m5_counterplay import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs, **kwargs: 0.30)
    obs = SimpleNamespace(street=Street.FLOP, to_call=0, pot=8, raises_this_street=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    assert bot.choose_action(obs, {}) == Action.CHECK_CALL


def test_value_bets_strong_postflop_equity(monkeypatch):
    from bots.m5_counterplay import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs, **kwargs: 0.85)
    obs = SimpleNamespace(street=Street.FLOP, to_call=0, pot=8, is_button=False,
                          raises_this_street=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    assert bot.choose_action(obs, {}) == Action.RAISE_POT


def test_preflop_uses_trained_equity_table(monkeypatch):
    from bots.m5_counterplay import bot
    from bots.common.cards import canonical_suits
    hand = (0, 4, 8, 12, 16)
    key = ';'.join(f'{r}{s}' for r, s in canonical_suits(hand))
    monkeypatch.setattr(bot, '_PREFLOP', {key: 0.85}, raising=False)
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    obs = SimpleNamespace(street=Street.PREFLOP, hole_cards=hand, is_button=True, to_call=1, pot=3, raises_this_street=0,
                          legal_actions=(Action.FOLD, Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    assert bot.choose_action(obs, {}) == Action.RAISE_POT


def test_opens_above_average_button_hand(monkeypatch):
    from bots.m5_counterplay import bot
    from bots.common.cards import canonical_suits
    hand = (0, 4, 8, 12, 16)
    key = ';'.join(f'{r}{s}' for r, s in canonical_suits(hand))
    monkeypatch.setattr(bot, '_PREFLOP', {key: 0.58})
    obs = SimpleNamespace(street=Street.PREFLOP, hole_cards=hand, is_button=True, to_call=1, pot=3, raises_this_street=0,
                          legal_actions=(Action.FOLD, Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    assert bot.choose_action(obs, {}) == Action.RAISE_HALF
