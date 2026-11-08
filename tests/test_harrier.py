from types import SimpleNamespace

from game import Action, Street
from league.run import match


def test_blocker_score_counts_paired_suited_and_top_rank_blockers():
    from bots.harrier import bot

    # Board: 8s 8c Kh (paired 8s, no 3-flush). Hole has one 8 (paired blocker)
    # and one K (top-rank blocker), plus two unrelated cards.
    obs = SimpleNamespace(hole_cards=(2 << 2 | 0, 7 << 2 | 1, 0, 1, 4), board=(2 << 2 | 1, 2 << 2 | 2, 7 << 2 | 0))
    assert bot._blocker_score(obs) == 2


def test_blocker_score_counts_flush_suit_blocker():
    from bots.harrier import bot

    # Board has three spades; hole has one spade.
    obs = SimpleNamespace(hole_cards=(0 << 2 | 3, 1, 2, 3, 4), board=(2 << 2 | 3, 3 << 2 | 3, 4 << 2 | 3))
    assert bot._blocker_score(obs) >= 1


def test_does_not_bluff_without_a_blocker(monkeypatch):
    from bots.harrier import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    monkeypatch.setattr(bot, '_blocker_score', lambda obs: 0)
    obs = SimpleNamespace(street=Street.RIVER, to_call=0, pot=8, hand_index=0, board=(0, 4, 8),
                           hole_cards=(1, 5, 9, 13, 17),
                           legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    memory = {'_hr_trials': {}, '_hr_folds': {}, '_hr_pending': None}
    assert bot.choose_action(obs, memory) == Action.CHECK_CALL
    assert memory['_hr_pending'] is None


def test_bluffs_river_with_a_blocker_when_checked_to(monkeypatch):
    from bots.harrier import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    monkeypatch.setattr(bot, '_blocker_score', lambda obs: 1)
    obs = SimpleNamespace(street=Street.RIVER, to_call=0, pot=8, hand_index=0, board=(0, 4, 8),
                           hole_cards=(1, 5, 9, 13, 17),
                           legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT))
    memory = {'_hr_trials': {}, '_hr_folds': {}, '_hr_pending': None}
    assert bot.choose_action(obs, memory) == Action.RAISE_HALF
    assert memory['_hr_pending'] == (0, Street.RIVER)


def test_spr_loosens_call_defense_when_short(monkeypatch):
    from bots.harrier import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.FOLD)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.40)
    # odds = 10/(20+10) = 0.333; flat Talon margin is 0.30 -> needs 0.633 to call.
    # SPR = min(stack)/pot = 15/20 = 0.75 <= 1.5 -> loosen by 0.07 -> needs 0.563.
    # equity=0.60 clears the loosened bar (0.563) but not the flat one (0.633).
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.60)
    obs = SimpleNamespace(street=Street.TURN, to_call=10, pot=20, my_stack=15, opp_stack=40,
                           hand_index=0, legal_actions=(Action.CHECK_CALL, Action.FOLD))
    memory = {'_hr_trials': {}, '_hr_folds': {}, '_hr_pending': None}
    assert bot.choose_action(obs, memory) == Action.CHECK_CALL


def test_spr_keeps_fold_when_deep(monkeypatch):
    from bots.harrier import bot

    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.FOLD)
    monkeypatch.setattr(bot.talon.base, 'estimate_equity', lambda obs, **kwargs: 0.40)
    # SPR = 80/20 = 4.0, below the SPR_TIGHT=5.0 cutoff so no shift applies;
    # equity 0.40 < odds(0.333) + 0.30 = 0.633, Talon's fold stands.
    obs = SimpleNamespace(street=Street.TURN, to_call=10, pot=20, my_stack=80, opp_stack=80,
                           hand_index=0, legal_actions=(Action.CHECK_CALL, Action.FOLD))
    memory = {'_hr_trials': {}, '_hr_folds': {}, '_hr_pending': None}
    assert bot.choose_action(obs, memory) == Action.FOLD


def test_plays_a_short_fresh_match_with_zero_errors():
    row = match('harrier', 'm5_challenger', 1, 150)
    assert row['errors'] == 0
    assert row['fallbacks'] == 0
    assert row['think_s'] < 8.0
