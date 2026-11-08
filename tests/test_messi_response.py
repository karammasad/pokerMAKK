from dataclasses import replace

import game
from bots.messi_response import bot
from bots.common.safe import wrap


def test_response_counts_once_across_streets():
    g = game.Game(game.make_deal('responses', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), street=game.Street.TURN, action_history=(
        game.ObservedAction(game.Street.FLOP, True, game.Action.RAISE_HALF, 5, 5),
        game.ObservedAction(game.Street.FLOP, False, game.Action.CHECK_CALL, 5, 5),
        game.ObservedAction(game.Street.TURN, True, game.Action.RAISE_HALF, 10, 10),
        game.ObservedAction(game.Street.TURN, False, game.Action.RAISE_POT, 30, 30),
    ))
    memory = {}
    bot._track_reraise_frequency(obs, memory)
    bot._track_reraise_frequency(obs, memory)
    assert memory['_rc_trials'] == 2
    assert memory['_rc_reraises'] == 1


def test_terminal_fold_counts_once():
    memory = {'_rc_pending': (3, game.Street.TURN)}
    result = game.HandResult(3, 5, 10, False, (), None, 'me')
    bot.on_hand_end(result, memory)
    bot.on_hand_end(result, memory)
    assert memory['_rc_trials'] == 1
    assert memory.get('_rc_reraises', 0) == 0


def test_legal_actions():
    bot.load()
    safe = wrap(bot)
    memory = {}
    safe.new_half(game.AgentConfig(num_hands=20), memory)
    for hand in range(20):
        g = game.Game(game.make_deal('response-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memory)
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memory)
    assert memory.get('_fallbacks', 0) == 0
