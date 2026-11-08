import importlib

import game
from bots.common.safe import wrap


def test_messi_v10_plays_legal_actions_and_isolates_half_state():
    bot = importlib.import_module('bots.messi_v10.bot')
    bot.load()
    safe = wrap(bot)
    memories = [{}, {}]
    for memory in memories:
        safe.new_half(game.AgentConfig(num_hands=20), memory)
    for hand in range(20):
        g = game.Game(game.make_deal('messi-v10-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memories[0])
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memories[0])
    assert memories[0] is not memories[1]
    assert memories[0].get('_fallbacks', 0) == 0


def test_messi_v10_still_folds_to_a_pot_sized_reraise_without_enough_equity(monkeypatch):
    from dataclasses import replace

    bot = importlib.import_module('bots.messi_v10.bot')
    g = game.Game(game.make_deal('messi-v10-rrcut-pot', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), street=game.Street.TURN,
                  board=(5, 6, 7, 8), pot=20, to_call=20, my_bet=5,
                  legal_actions=(game.Action.FOLD, game.Action.CHECK_CALL, game.Action.RAISE_HALF),
                  raise_to={game.Action.RAISE_HALF: 60},
                  action_history=(
                      game.ObservedAction(game.Street.TURN, True, game.Action.RAISE_HALF, 5, 5),
                      game.ObservedAction(game.Street.TURN, False, game.Action.RAISE_POT, 25, 25),
                  ))
    monkeypatch.setattr(bot.attack.base.base, 'estimate_equity', lambda *a, **k: 0.70)
    action = bot._base_choose_action(obs, {'_think_s': 0.0})
    assert action == game.Action.FOLD


def test_messi_v10_continues_against_a_half_pot_reraise_with_moderate_equity(monkeypatch):
    from dataclasses import replace

    bot = importlib.import_module('bots.messi_v10.bot')
    g = game.Game(game.make_deal('messi-v10-rrcut-half', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), street=game.Street.TURN,
                  board=(5, 6, 7, 8), pot=20, to_call=10, my_bet=5,
                  legal_actions=(game.Action.FOLD, game.Action.CHECK_CALL, game.Action.RAISE_HALF),
                  raise_to={game.Action.RAISE_HALF: 40},
                  action_history=(
                      game.ObservedAction(game.Street.TURN, True, game.Action.RAISE_HALF, 5, 5),
                      game.ObservedAction(game.Street.TURN, False, game.Action.RAISE_HALF, 10, 10),
                  ))
    monkeypatch.setattr(bot.attack.base.base, 'estimate_equity', lambda *a, **k: 0.70)
    action = bot._base_choose_action(obs, {'_think_s': 0.0})
    assert action == game.Action.CHECK_CALL


def test_messi_v10_thins_value_against_a_detected_station(monkeypatch):
    from dataclasses import replace

    bot = importlib.import_module('bots.messi_v10.bot')
    g = game.Game(game.make_deal('messi-v10-station', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), street=game.Street.RIVER,
                  board=(5, 6, 7, 8, 9), pot=20, to_call=0, my_bet=0,
                  legal_actions=(game.Action.CHECK_CALL, game.Action.RAISE_HALF, game.Action.RAISE_POT),
                  action_history=())
    memory = {'_think_s': 0.0, '_st_made': 70, '_st_folded': 0}
    monkeypatch.setattr(bot.attack.base.base, 'estimate_equity', lambda *a, **k: 0.36)
    action = bot._base_choose_action(obs, memory)
    assert action == game.Action.RAISE_HALF
    assert not bot._is_station({'_st_made': 69, '_st_folded': 0})
