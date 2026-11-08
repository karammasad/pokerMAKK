from types import SimpleNamespace

from game import Action, Street


def test_bluffs_weak_river_hand_when_checked_to(monkeypatch):
    from bots.m5_classic import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs: 0.1)
    obs = SimpleNamespace(street=Street.RIVER, to_call=0,
                          legal_actions=[Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT],
                          action_history=[SimpleNamespace(is_me=False, street=Street.RIVER, action=Action.CHECK_CALL)])
    assert bot.choose_action(obs, {}) == Action.RAISE_HALF


def test_folds_marginal_postflop_call_facing_bet(monkeypatch):
    from bots.m5_classic import bot
    monkeypatch.setattr(bot.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.base, 'estimate_equity', lambda obs: 0.40)
    obs = SimpleNamespace(street=Street.FLOP, to_call=10, pot=30,
                          legal_actions=[Action.FOLD, Action.CHECK_CALL])
    assert bot.choose_action(obs, {}) == Action.FOLD
