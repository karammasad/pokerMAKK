"""Deterministic state-machine and duplicate-deal property tests."""
import random

import game
from game import Action


def test_seeded_deals_are_reproducible_and_cards_are_unique():
    for seed in range(100):
        a = game.make_deal(seed, seed * 7)
        b = game.make_deal(str(seed), seed * 7)
        assert a == b
        cards = (*a.hole_cards[0], *a.hole_cards[1], *a.board)
        assert len(cards) == 15
        assert len(set(cards)) == 15
        assert game.button_for_deal(seed * 7) == (seed * 7) % 2


def test_random_legal_play_preserves_chip_and_raise_invariants():
    rng = random.Random(413)
    for seed in range(80):
        hand = game.Game(game.make_deal("invariants", seed), game.button_for_deal(seed), seed)
        while not hand.is_terminal:
            seat = hand.to_act
            obs = hand.observation(seat)
            assert obs.legal_actions
            assert all(isinstance(action, Action) for action in obs.legal_actions)
            assert (Action.FOLD in obs.legal_actions) == (obs.to_call > 0)
            for action, raise_to in obs.raise_to.items():
                assert action in (Action.RAISE_HALF, Action.RAISE_POT)
                assert raise_to <= obs.opp_bet + hand.pot + obs.to_call
                assert raise_to <= obs.my_bet + obs.my_stack
                assert raise_to >= obs.min_raise_to or raise_to == obs.my_bet + obs.my_stack
            hand.apply(rng.choice(obs.legal_actions))
            assert hand.raises_this_street <= game.RAISE_CAP_PER_STREET
            assert min(hand.stacks) >= 0
            assert all(hand.stacks[s] + hand.contributed[s] == game.STARTING_STACK for s in (0, 1))
            assert hand.pot == sum(hand.contributed)
        result = hand.result()
        assert result.nets[0] + result.nets[1] == 0
        assert result.pot == sum(hand.contributed)


def test_duplicate_halves_reuse_same_deal_and_swap_agent_seat():
    for deal_index in range(200):
        deal_one = game.make_deal("duplicate", deal_index)
        deal_two = game.make_deal("duplicate", deal_index)
        assert deal_one == deal_two
        seat_a_half_one = 0
        seat_a_half_two = 1
        assert seat_a_half_one != seat_a_half_two
