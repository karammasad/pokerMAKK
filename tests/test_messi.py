import importlib

import game
from bots.common.safe import wrap


def test_messi_plays_legal_actions_and_isolates_half_state():
    bot = importlib.import_module('bots.messi.bot')
    bot.load()
    safe = wrap(bot)
    memories = [{}, {}]
    for memory in memories:
        safe.new_half(game.AgentConfig(num_hands=20), memory)
    for hand in range(20):
        g = game.Game(game.make_deal('messi-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memories[0])
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memories[0])
    assert memories[0] is not memories[1]
    assert memories[0].get('_fallbacks', 0) == 0
    assert memories[1].get('_think_s', 0) == 0


def test_messi_keeps_playing_legally_after_nearing_time_budget(monkeypatch):
    bot = importlib.import_module('bots.messi.bot')
    bot.load()
    safe = wrap(bot)
    memory = {}
    safe.new_half(game.AgentConfig(), memory)
    memory['_think_s'] = 2.0
    samples = []
    estimate = bot.attack.base.base.estimate_equity
    def track(obs, budget_s=None, max_samples=32):
        samples.append(max_samples)
        return estimate(obs, budget_s=budget_s, max_samples=max_samples)
    monkeypatch.setattr(bot.attack.base.base, 'estimate_equity', track)
    for hand in range(20):
        g = game.Game(game.make_deal('messi-budget', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memory)
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memory)
    assert memory['_fallbacks'] == 0
    assert 8 in samples


def test_messi_reraises_only_when_observed_responses_support_it(monkeypatch):
    from dataclasses import replace

    bot = importlib.import_module('bots.messi.bot')
    monkeypatch.setattr(bot, '_base_choose_action', lambda obs, memory: game.Action.FOLD)
    g = game.Game(game.make_deal('messi-reraise', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), street=game.Street.TURN,
                  board=(5, 6, 7, 8), pot=20, to_call=5, my_bet=0,
                  legal_actions=(game.Action.FOLD, game.Action.CHECK_CALL, game.Action.RAISE_HALF),
                  raise_to={game.Action.RAISE_HALF: 25},
                  action_history=(game.ObservedAction(game.Street.TURN, False,
                                                       game.Action.RAISE_HALF, 5, 5),))
    # No automatic bluff before the opponent has shown a fold tendency.
    assert bot.choose_action(obs, {}) == game.Action.FOLD
    folds_often = {'_rr_trials': 12, '_rr_folds': 10}
    calls_often = {'_rr_trials': 12, '_rr_folds': 2}
    assert bot.choose_action(obs, folds_often) == game.Action.RAISE_HALF
    assert bot.choose_action(obs, calls_often) == game.Action.FOLD
    result = game.HandResult(obs.hand_index, 20, 20, False, obs.board, None, 'me')
    bot.on_hand_end(result, folds_often)
    assert folds_often['_rr_trials'] == 13
    assert folds_often['_rr_folds'] == 11
