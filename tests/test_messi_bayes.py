import game
from bots.messi_bayes import bot


def test_response_threshold_starts_conservative_and_adapts_smoothly():
    memory = {'_rc_trials': 0, '_rc_reraises': 0}
    prior = bot._rr_cut_equity(memory)
    assert prior == 0.85
    memory.update(_rc_trials=30, _rc_reraises=18)
    aggressive = bot._rr_cut_equity(memory)
    assert 0.50 < aggressive < prior
    memory.update(_rc_trials=30, _rc_reraises=0)
    selective = bot._rr_cut_equity(memory)
    assert selective > aggressive


def test_module_inherits_v7_legal_action_behavior():
    bot.load()
    safe = __import__('bots.common.safe', fromlist=['wrap']).wrap(bot)
    memory = {}
    safe.new_half(game.AgentConfig(num_hands=12), memory)
    for hand in range(12):
        g = game.Game(game.make_deal('messi-bayes-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memory)
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memory)
    assert memory.get('_fallbacks', 0) == 0
