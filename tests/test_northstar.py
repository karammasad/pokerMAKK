from types import SimpleNamespace
from unittest.mock import patch

from bots.northstar import bot
from game import Action, Street


def observation(hand, legal=(Action.FOLD, Action.CHECK_CALL)):
    return SimpleNamespace(street=Street.RIVER, to_call=10, pot=25,
                           legal_actions=legal, hand_index=hand)


def test_river_guard_requires_evidence_and_keeps_exploration():
    memory = {'_ns_river_trials': 11, '_ns_river_wins': 0.0, '_ns_river_pending': None}
    with patch.object(bot.base, 'choose_action', return_value=Action.CHECK_CALL), patch.object(bot, '_explore', side_effect=lambda obs: obs.hand_index == 5):
        assert bot.choose_action(observation(1), memory) == Action.CHECK_CALL
        memory['_ns_river_trials'] = 12
        assert bot.choose_action(observation(2), memory) == Action.FOLD
        assert bot.choose_action(observation(5), memory) == Action.CHECK_CALL
        assert bot.choose_action(observation(6, (Action.CHECK_CALL,)), memory) == Action.CHECK_CALL
        memory['_ns_river_wins'] = 8
        assert bot.choose_action(observation(7), memory) == Action.CHECK_CALL


def test_only_pending_showdown_updates_win_rate():
    memory = {'_ns_river_trials': 0, '_ns_river_wins': 0.0, '_ns_river_pending': 10}
    with patch.object(bot.base, 'on_hand_end'):
        bot.on_hand_end(SimpleNamespace(hand_index=10, went_to_showdown=True, winner='split'), memory)
        assert memory['_ns_river_trials'] == 1
        assert memory['_ns_river_wins'] == 0.5
        assert memory['_ns_river_pending'] is None
        bot.on_hand_end(SimpleNamespace(hand_index=11, went_to_showdown=True, winner='me'), memory)
        assert memory['_ns_river_trials'] == 1


def test_late_half_uses_small_equity_sample_and_tracks_history():
    memory = {'_think_s': 1.3}
    obs = SimpleNamespace(street=Street.TURN, to_call=10, pot=30,
                          hole_cards=(1, 2, 3, 4, 5), board=(6, 7, 8, 9),
                          legal_actions=(Action.FOLD, Action.CHECK_CALL))
    with patch.object(bot.base, '_observe') as observe, \
         patch.object(bot.base, '_finish_action', side_effect=lambda obs, memory, action: action), \
         patch.object(bot, 'equity_vs_random', return_value=0.2) as equity:
        assert bot.choose_action(obs, memory) == Action.FOLD
        observe.assert_called_once_with(obs, memory)
        assert equity.call_args.args[2] == 8
