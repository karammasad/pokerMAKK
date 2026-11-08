from dataclasses import replace
import game
from bots.atlas_learning import bot


def obs():
    g = game.Game(game.make_deal('atlas-learning', 0), 0, 0)
    return replace(g.observation(g.to_act), street=game.Street.RIVER,
                   board=(5, 6, 7, 8, 9), pot=30, to_call=10,
                   legal_actions=(game.Action.FOLD, game.Action.CHECK_CALL),
                   action_history=(game.ObservedAction(game.Street.RIVER, True,
                                                       game.Action.RAISE_HALF, 5, 5),
                                   game.ObservedAction(game.Street.RIVER, False,
                                                       game.Action.RAISE_POT, 15, 15)))


def test_learning_stops_bad_calls_but_preserves_sparse_and_good_calls(monkeypatch):
    monkeypatch.setattr(bot.base, 'choose_action', lambda o, m: game.Action.CHECK_CALL)
    monkeypatch.setattr(bot, 'estimate', lambda *args: 0.65)
    monkeypatch.setattr(bot.base, 'on_hand_end', lambda *args: None)
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    o = obs()
    assert bot.choose_action(o, memory) == game.Action.CHECK_CALL
    for hand in range(12):
        o = replace(o, hand_index=hand)
        bot.choose_action(o, memory)
        bot.on_hand_end(game.HandResult(hand, -20, 40, True, o.board, (10,11,12,13,14), 'opp'), memory)
    assert bot.choose_action(replace(o, hand_index=12), memory) == game.Action.FOLD
    assert memory['_atlas_learning']['blocked'] > 0
    # New half must not inherit the previous opponent's learning.
    bot.new_half(game.AgentConfig(), memory)
    assert bot.choose_action(o, memory) == game.Action.CHECK_CALL


def test_recovery_probes_are_bounded_and_never_override_value(monkeypatch):
    monkeypatch.setattr(bot.base, 'choose_action', lambda o, m: game.Action.CHECK_CALL)
    monkeypatch.setattr(bot, 'estimate', lambda *args: 0.65)
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    o = obs()
    cell = bot._cell(memory['_atlas_learning'], 0.25)
    cell['outcomes'] = [(0.0, 0.25)] * 12
    actions = [bot.choose_action(replace(o, hand_index=i), memory) for i in range(8)]
    assert actions.count(game.Action.CHECK_CALL) == 1
    assert memory['_atlas_learning']['probes'] == 1
    cheap = replace(o, to_call=3, pot=97)
    assert bot.choose_action(cheap, memory) == game.Action.CHECK_CALL
    monkeypatch.setattr(bot, 'estimate', lambda *args: 0.90)
    assert bot.choose_action(o, memory) == game.Action.CHECK_CALL
    monkeypatch.setattr(bot, 'estimate', lambda *args: 0.65)
    big = replace(o, to_call=40, pot=120)
    cell['blocked'] = 7
    assert bot.choose_action(big, memory) == game.Action.FOLD


def test_ordinary_call_feedback_is_separate_from_reraises(monkeypatch):
    monkeypatch.setattr(bot.base, 'choose_action', lambda o, m: game.Action.CHECK_CALL)
    monkeypatch.setattr(bot, 'estimate', lambda *args: 0.65)
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    o = obs()
    bot._cell(memory['_atlas_learning'], 0.25, True)['outcomes'] = [(0.0,0.25)]*16
    ordinary = replace(o, action_history=(o.action_history[-1],))
    assert bot.choose_action(ordinary, memory) == game.Action.CHECK_CALL
    assert bot.choose_action(o, memory) == game.Action.FOLD
