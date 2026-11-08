from types import SimpleNamespace

from game import Action, Street


def test_turn_opportunity_places_small_bluff(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(counter_strategies.base.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    obs = SimpleNamespace(street=Street.TURN, hand_index=5, to_call=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    assert counter_strategies.choose_action(obs, {}, 'turnblade') == Action.RAISE_HALF


def test_adaptive_strategy_stops_bluffing_when_opponent_never_folds(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(counter_strategies.base.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    obs = SimpleNamespace(street=Street.TURN, hand_index=5, to_call=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    memory = {'_cs_trials': 20, '_cs_folds': 0}
    assert counter_strategies.choose_action(obs, memory, 'm5_challenger') == Action.CHECK_CALL


def test_nightjar_limits_early_and_river_bluffs(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    monkeypatch.setattr(counter_strategies.base.base, 'estimate_equity', lambda obs, **kwargs: 0.20)
    obs = SimpleNamespace(street=Street.RIVER, hand_index=1, hole_cards=(0, 4, 8, 12, 16), to_call=0,
                          legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    assert counter_strategies.choose_action(obs, {}, 'nightjar') == Action.CHECK_CALL


def test_mirrorfin_does_not_make_a_very_loose_river_call(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.FOLD)
    monkeypatch.setattr(counter_strategies.base.base, 'estimate_equity', lambda obs, **kwargs: 0.52)
    obs = SimpleNamespace(street=Street.RIVER, hand_index=1, to_call=10, pot=30,
                          legal_actions=(Action.FOLD, Action.CHECK_CALL))
    assert counter_strategies.choose_action(obs, {}, 'mirrorfin') == Action.FOLD


def test_tidehunter_mixes_rather_than_always_opening_marginal_hands(monkeypatch):
    from bots.common import counter_strategies
    from bots.common.cards import canonical_suits
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    hand = (0, 4, 8, 12, 16)
    key = ';'.join(f'{r}{s}' for r, s in canonical_suits(hand))
    monkeypatch.setattr(counter_strategies.base, '_PREFLOP', {key: 0.52})
    obs = SimpleNamespace(street=Street.PREFLOP, hand_index=1, hole_cards=hand, is_button=True,
                          raises_this_street=0, to_call=1, legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF))
    assert counter_strategies.choose_action(obs, {}, 'tidehunter') == Action.CHECK_CALL


def test_adaptive_counts_fold_when_bet_ends_hand(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'on_hand_end', lambda result, memory: None)
    memory = {'_cs_trials': 0, '_cs_folds': 0, '_cs_pending': 4}
    result = SimpleNamespace(hand_index=4, went_to_showdown=False, winner='me')
    counter_strategies.on_hand_end(result, memory)
    assert (memory['_cs_trials'], memory['_cs_folds'], memory['_cs_pending']) == (1, 1, None)


def test_adaptive_counts_continuation_without_counting_a_fold(monkeypatch):
    from bots.common import counter_strategies
    monkeypatch.setattr(counter_strategies.base, 'choose_action', lambda obs, memory: Action.CHECK_CALL)
    obs = SimpleNamespace(street=Street.FLOP, hand_index=4, to_call=0,
                          legal_actions=(Action.CHECK_CALL,))
    memory = {'_cs_trials': 0, '_cs_folds': 0, '_cs_pending': 4}
    assert counter_strategies.choose_action(obs, memory, 'm5_challenger') == Action.CHECK_CALL
    assert (memory['_cs_trials'], memory['_cs_folds'], memory['_cs_pending']) == (1, 0, None)
