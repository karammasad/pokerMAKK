"""In-process league consistency checks; HTTP equivalence is exercised separately."""
from league.run import load_bot, play_half
from bots.common.safe import wrap


def test_same_seed_is_reproducible_and_zero_sum():
    def play():
        a = wrap(load_bot("m1_equity"))
        b = wrap(load_bot("random"))
        first, err1, _ = play_half(a, b, "league-check", 1, 12)
        second, err2, _ = play_half(a, b, "league-check", 2, 12)
        assert err1 == err2 == 0
        return [first[i] + second[i] for i in range(12)]
    assert play() == play()
