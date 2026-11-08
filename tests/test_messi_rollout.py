import game
from bots.messi_rollout import bot


def test_fold_prob_blends_prior_with_observations_and_stays_bounded():
    memory = {"_rollout_fold_obs": {}}
    obs_class = type("O", (), {"street": game.Street.FLOP})()
    from game import Action
    p_prior = bot._fold_prob(obs_class, memory, Action.RAISE_HALF)
    assert 0.03 <= p_prior <= 0.65
    memory["_rollout_fold_obs"]["FLOP"] = (20, 20)
    p_high = bot._fold_prob(obs_class, memory, Action.RAISE_HALF)
    assert p_high > p_prior


def test_module_runs_full_hands_with_legal_actions_and_no_fallbacks():
    bot_mod = bot
    safe = __import__('bots.common.safe', fromlist=['wrap']).wrap(bot_mod)
    memory = {}
    safe.new_half(game.AgentConfig(num_hands=15), memory)
    for hand in range(15):
        g = game.Game(game.make_deal('messi-rollout-test', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memory)
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memory)
    assert memory.get('_fallbacks', 0) == 0
