from dataclasses import replace

import game
from bots.atlas import bot
from bots.common.safe import wrap


def observation():
    g = game.Game(game.make_deal('atlas-response', 0), 0, 0)
    return g.observation(g.to_act)


def test_terminal_fold_is_counted_once_and_half_state_resets(monkeypatch):
    monkeypatch.setattr(bot.core, 'choose_action', lambda p, obs, m: game.Action.RAISE_HALF)
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    obs = observation()
    assert bot.choose_action(obs, memory) == game.Action.RAISE_HALF
    result = game.HandResult(0, 2, 6, False, (), None, 'me')
    bot.on_hand_end(result, memory)
    bot.on_hand_end(result, memory)
    assert bot._cell(memory['_atlas'], obs.street, game.Action.RAISE_HALF) == [1, 1, 0]
    bot.new_half(game.AgentConfig(), memory)
    assert memory['_atlas']['responses'] == {}


def test_observed_reraise_is_not_counted_again_at_hand_end(monkeypatch):
    monkeypatch.setattr(bot.core, 'choose_action', lambda p, obs, m: game.Action.RAISE_HALF)
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    obs = observation()
    bot.choose_action(obs, memory)
    obs = replace(obs, action_history=(
        game.ObservedAction(obs.street, True, game.Action.RAISE_HALF, 3, 4),
        game.ObservedAction(obs.street, False, game.Action.RAISE_POT, 10, 12)))
    monkeypatch.setattr(bot.core, 'choose_action', lambda p, obs, m: game.Action.FOLD)
    bot.choose_action(obs, memory)
    bot.on_hand_end(game.HandResult(0, -4, 16, False, (), None, 'opp'), memory)
    assert bot._cell(memory['_atlas'], obs.street, game.Action.RAISE_HALF) == [1, 0, 1]


def test_full_hands_have_no_hidden_fallbacks_and_charge_callbacks():
    bot.load()
    safe = wrap(bot)
    memory = {}
    safe.new_half(game.AgentConfig(num_hands=25), memory)
    for hand in range(25):
        g = game.Game(game.make_deal('atlas-legal', hand), game.button_for_deal(hand), hand)
        while not g.is_terminal:
            obs = g.observation(g.to_act)
            action = safe.choose_action(obs, memory)
            assert action in obs.legal_actions
            g.apply(action)
        safe.on_hand_end(g.hand_result(0), memory)
    assert memory['_fallbacks'] == 0
    assert memory['_atlas']['callback_s'] > 0


def test_prefix_sampling_matches_official_sampler_and_clears_between_hands():
    import random
    from bots.atlas.equity import estimate
    from bots.common.equity import equity_vs_random
    rng = random.Random(14001)
    memory = {}
    original = observation()
    for hand in range(8):
        cards = rng.sample(range(36), 10)
        for street, count in ((game.Street.FLOP, 3), (game.Street.TURN, 4), (game.Street.RIVER, 5)):
            obs = replace(original, hand_index=hand, street=street,
                          hole_cards=tuple(cards[:5]), board=tuple(cards[5:5 + count]))
            for samples in (8, 32, 80, 16):
                assert estimate(obs, memory, samples) == equity_vs_random(obs.hole_cards, obs.board, samples)
        assert len(memory['_atlas_eq']) == 3


def test_bluff_reraise_requires_context_evidence_and_actual_cost(monkeypatch):
    monkeypatch.setattr(bot.core, 'choose_action', lambda p, obs, m: game.Action.FOLD)
    obs = replace(observation(), street=game.Street.TURN, board=(5, 6, 7, 8),
                  pot=20, to_call=5, my_bet=0,
                  legal_actions=(game.Action.FOLD, game.Action.CHECK_CALL, game.Action.RAISE_HALF),
                  raise_to={game.Action.RAISE_HALF: 25},
                  action_history=(game.ObservedAction(game.Street.TURN, False,
                                                      game.Action.RAISE_HALF, 5, 5),))
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    assert bot.choose_action(obs, memory) == game.Action.FOLD
    bot._cell(memory['_atlas'], obs.street, game.Action.RAISE_HALF, False)[:] = [50, 48, 0]
    assert bot.choose_action(obs, memory) == game.Action.FOLD  # ordinary bet data is insufficient
    bot._cell(memory['_atlas'], obs.street, game.Action.RAISE_HALF, True)[:] = [50, 48, 0]
    assert bot.choose_action(obs, memory) == game.Action.RAISE_HALF
    expensive = replace(obs, raise_to={game.Action.RAISE_HALF: 200})
    assert bot.choose_action(expensive, memory) == game.Action.FOLD


def test_reraise_defense_requires_repeated_matching_street_evidence(monkeypatch):
    profiles = []
    monkeypatch.setattr(bot.core, 'choose_action',
                        lambda p, obs, m: profiles.append(dict(p)) or game.Action.FOLD)
    obs = replace(observation(), street=game.Street.TURN, board=(5, 6, 7, 8),
                  pot=30, to_call=10,
                  action_history=(game.ObservedAction(game.Street.TURN, True,
                                                       game.Action.RAISE_HALF, 5, 5),
                                  game.ObservedAction(game.Street.TURN, False,
                                                       game.Action.RAISE_POT, 15, 15)))
    memory = {}
    bot.new_half(game.AgentConfig(), memory)
    bot._cell(memory['_atlas'], game.Street.FLOP, game.Action.RAISE_HALF)[:] = [50, 0, 30]
    bot.choose_action(obs, memory)
    assert profiles[-1]['rr_cut'] is not None
    bot._cell(memory['_atlas'], game.Street.TURN, game.Action.RAISE_HALF)[:] = [50, 0, 30]
    bot.choose_action(obs, memory)
    assert profiles[-1]['rr_cut'] is None
    assert profiles[-1]['call_margin'] == 0.20


def test_aggressor_snapshot_matches_classic_before_time_guard():
    import gzip
    import json
    from pathlib import Path
    from types import SimpleNamespace
    from bots.m5_classic import bot as classic
    bot.load()
    reference = wrap(classic)
    optimized = wrap(SimpleNamespace(new_half=bot.new_half, choose_action=bot.core._aggressor))
    memories = [{}, {}]
    reference.new_half(game.AgentConfig(), memories[0])
    optimized.new_half(game.AgentConfig(), memories[1])
    count = 0
    with gzip.open(Path(__file__).parent / 'fixtures/decision_states.jsonl.gz', 'rt') as f:
        for line in f:
            obs = game.Observation.from_dict(json.loads(line)['observation'])
            if obs.street == game.Street.PREFLOP:
                continue
            assert optimized.choose_action(obs, memories[1]) == reference.choose_action(obs, memories[0])
            count += 1
            if count == 100:
                break
    assert all(m['_fallbacks'] == 0 for m in memories)
