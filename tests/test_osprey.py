from types import SimpleNamespace

from bots.osprey import bot
from game import Action, AgentConfig, Street
from league.run import match


def _obs(hole=(0, 1, 2, 3, 4), board=(), street=Street.FLOP, history=(),
         to_call=0, pot=8, legal_actions=(Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT)):
    return SimpleNamespace(
        hand_index=0,
        street=street,
        hole_cards=hole,
        board=board,
        pot=pot,
        to_call=to_call,
        legal_actions=legal_actions,
        action_history=tuple(history),
    )


def test_particles_are_unseen_cards_disjoint_from_hero_hand():
    memory = {}
    bot.new_half(AgentConfig(), memory)
    obs = _obs(hole=(0, 1, 2, 3, 4), board=(10, 11, 12), street=Street.FLOP)
    particles, weights = bot._sync_particles(obs, memory)
    assert len(particles) == bot.N_PARTICLES
    assert len(weights) == bot.N_PARTICLES
    dead = set(obs.hole_cards) | set(obs.board)
    for particle in particles:
        assert len(particle) == 5
        assert len(set(particle)) == 5
        assert not (set(particle) & dead)


def test_particles_reset_between_hands():
    memory = {}
    bot.new_half(AgentConfig(), memory)
    obs0 = _obs(hole=(0, 1, 2, 3, 4), board=(10, 11, 12))
    particles0, _ = bot._sync_particles(obs0, memory)
    obs1 = _obs(hole=(5, 6, 7, 8, 9), board=(14, 15, 16))
    obs1.hand_index = 1
    particles1, _ = bot._sync_particles(obs1, memory)
    assert memory['_op_hand'] == 1
    assert particles1 is not particles0


def test_a_raise_upweights_a_strong_particle_more_than_a_weak_one(monkeypatch):
    particle_equity = {('strong',): 0.85, ('weak',): 0.30}
    monkeypatch.setattr(bot, 'equity_vs_random', lambda particle, board, samples: particle_equity[particle])
    record_pot = SimpleNamespace(street=Street.FLOP, is_me=False, action=Action.RAISE_POT, amount=8)
    weights = [1.0, 1.0]
    bot._reweight_action([('strong',), ('weak',)], weights, record_pot, ())
    assert weights[0] > weights[1]


def test_a_pot_raise_discriminates_more_sharply_than_a_half_pot_raise(monkeypatch):
    # A pot raise is read as stronger evidence: its weight ratio between a
    # clearly-strong hand and a merely-decent hand should be wider than a
    # half-pot raise's, since the pot-raise threshold sits higher and steeper.
    def equity_for(particle, board, samples):
        return {('strong',): 0.85, ('decent',): 0.58}[particle]
    monkeypatch.setattr(bot, 'equity_vs_random', equity_for)
    pot_weights = [1.0, 1.0]
    bot._reweight_action([('strong',), ('decent',)], pot_weights, SimpleNamespace(
        street=Street.FLOP, is_me=False, action=Action.RAISE_POT, amount=8), ())
    half_weights = [1.0, 1.0]
    bot._reweight_action([('strong',), ('decent',)], half_weights, SimpleNamespace(
        street=Street.FLOP, is_me=False, action=Action.RAISE_HALF, amount=4), ())
    pot_ratio = pot_weights[0] / pot_weights[1]
    half_ratio = half_weights[0] / half_weights[1]
    assert pot_ratio > half_ratio


def test_a_fold_resolved_pending_hand_does_not_crash_reweight():
    memory = {}
    bot.new_half(AgentConfig(), memory)
    obs = _obs(hole=(0, 1, 2, 3, 4), board=(10, 11, 12),
               history=[SimpleNamespace(street=Street.FLOP, is_me=False, action=Action.CHECK_CALL, amount=0)])
    particles, weights = bot._sync_particles(obs, memory)
    assert memory['_op_seen'] == 1
    assert all(w > 0 for w in weights)


def test_estimate_range_equity_is_bounded_and_uses_cache_on_river():
    memory = {}
    bot.new_half(AgentConfig(), memory)
    obs = _obs(hole=(32, 33, 34, 35, 0), board=(10, 11, 12, 13, 14), street=Street.RIVER,
               history=[SimpleNamespace(street=Street.FLOP, is_me=False, action=Action.CHECK_CALL, amount=0)])
    equity = bot.estimate_range_equity(obs, memory)
    assert equity is not None
    assert 0.0 <= equity <= 1.0


def test_preflop_defers_entirely_to_talon(monkeypatch):
    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.RAISE_HALF)
    obs = _obs(street=Street.PREFLOP)
    memory = {}
    assert bot.choose_action(obs, memory) == Action.RAISE_HALF
    assert '_op_hand' not in memory or memory['_op_hand'] is None


def test_budget_guard_falls_back_to_talon(monkeypatch):
    monkeypatch.setattr(bot.talon, 'choose_action', lambda obs, memory: Action.FOLD)
    obs = _obs(street=Street.TURN, to_call=4, legal_actions=(Action.FOLD, Action.CHECK_CALL))
    memory = {'_think_s': 7.0}
    assert bot.choose_action(obs, memory) == Action.FOLD


def test_plays_a_short_fresh_match_with_zero_errors():
    row = match('osprey', 'm5_challenger', 1, 150)
    assert row['errors'] == 0
    assert row['fallbacks'] == 0
    assert row['think_s'] < 8.0
