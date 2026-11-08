from unittest.mock import patch
from league import run


def test_opponent_fallbacks_follow_seat_swap():
    def play(a, b, seed, half, deals):
        ours = {'_fallbacks': half, '_think_s': float(half), '_decision_ms': [0.1]}
        theirs = {'_fallbacks': half + 2, '_think_s': float(half + 2)}
        return [0, 0], 0, [ours, theirs] if half == 1 else [theirs, ours]
    with patch.object(run, 'load_bot', return_value=object()), \
         patch.object(run, 'wrap', side_effect=lambda bot: bot), \
         patch.object(run, 'play_half', side_effect=play):
        result = run.match('a', 'b', 1, 2)
    assert result['fallbacks'] == 3
    assert result['opponent_fallbacks'] == 7
    assert (result['opponent_think_h1_s'], result['opponent_think_h2_s']) == (3.0, 4.0)
