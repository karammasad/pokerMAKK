import game
from bots.messi_showdownrange import bot
from bots.common.safe import wrap


def test_range_candidate_legal_actions_and_memory_isolation():
    bot.load()
    safe = wrap(bot)
    memories = [{}, {}]
    for memory in memories:
        safe.new_half(game.AgentConfig(num_hands=16), memory)
    for hand in range(16):
        g = game.Game(game.make_deal('showdown-range-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memories[0])
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memories[0])
    assert memories[0].get('_fallbacks', 0) == 0
    assert memories[1]['_m6_range_examples'] == []
