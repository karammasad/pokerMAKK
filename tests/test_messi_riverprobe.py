from dataclasses import replace
import game
from bots.messi_riverprobe import bot
from bots.common.safe import wrap


def test_probe_requires_fold_evidence_and_legal_raise(monkeypatch):
    monkeypatch.setattr(bot.baseline, 'choose_action', lambda obs, mem: game.Action.CHECK_CALL)
    monkeypatch.setattr(bot.baseline.attack.base.base, 'estimate_equity', lambda *a, **kw: 0.2)
    g = game.Game(game.make_deal('riverprobe', 0), game.button_for_deal(0), 0)
    obs = replace(g.observation(g.to_act), hand_index=0, street=game.Street.RIVER,
                  hole_cards=(0, 1, 2, 3, 6), board=(4, 5, 7, 8, 9), pot=100,
                  to_call=0, my_bet=0, legal_actions=(game.Action.CHECK_CALL, game.Action.RAISE_HALF),
                  raise_to={game.Action.RAISE_HALF: 50})
    memory = {'_rp_trials': 12, '_rp_folds': 10, '_rp_pending': None}
    assert bot.choose_action(obs, memory) == game.Action.RAISE_HALF
    assert memory['_rp_pending'] == 0
    assert bot.choose_action(replace(obs, to_call=20), memory) == game.Action.CHECK_CALL
    assert memory['_rp_trials'] == 13
    memory = {'_rp_trials': 11, '_rp_folds': 11, '_rp_pending': None}
    assert bot.choose_action(obs, memory) == game.Action.CHECK_CALL


def test_safe_actions_and_half_isolation():
    bot.load()
    safe = wrap(bot)
    memories = [{}, {}]
    for memory in memories:
        safe.new_half(game.AgentConfig(num_hands=20), memory)
    for hand in range(20):
        g = game.Game(game.make_deal('riverprobe-legal', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memories[0])
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memories[0])
    assert memories[0].get('_fallbacks', 0) == 0
    assert memories[1]['_rp_trials'] == 0
