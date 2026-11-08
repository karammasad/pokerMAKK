import importlib

import game
from bots.common.safe import wrap


def test_messi_v7_plays_legal_actions_and_isolates_half_state():
    bot = importlib.import_module('bots.messi_v7.bot')
    bot.load()
    safe = wrap(bot)
    memories = [{}, {}]
    for memory in memories:
        safe.new_half(game.AgentConfig(num_hands=20), memory)
    for hand in range(20):
        g = game.Game(game.make_deal('messi-v7-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memories[0])
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memories[0])
    assert memories[0] is not memories[1]
    assert memories[0].get('_fallbacks', 0) == 0

