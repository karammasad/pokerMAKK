import pytest

from league import run

CITY = ["haaland", "de_bruyne", "rodri", "foden", "bernardo", "grealish",
        "doku", "stones", "akanji", "ederson", "mahrez", "gundogan", "aguero"]


@pytest.mark.parametrize("name", CITY)
def test_city_bot_plays_legally_without_errors(name):
    for opp in ("maniac", "calling_station", "m5_counterplay"):
        row = run.match(name, opp, 5, 60)
        assert row["errors"] == 0 and row["fallbacks"] == 0
