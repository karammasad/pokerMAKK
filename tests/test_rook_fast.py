"""The speed variant must preserve Rook's policy on diverse observations."""
import gzip
import json
from pathlib import Path

from bots.m11_chosen import bot as rook
from bots.rook_fast import bot as fast
from game import AgentConfig, Observation


def test_fast_rook_matches_original_on_state_corpus():
    rook.load()
    fast.load()
    original_memory, fast_memory = {}, {}
    rook.new_half(AgentConfig(), original_memory)
    fast.new_half(AgentConfig(), fast_memory)
    path = Path(__file__).parent / 'fixtures/decision_states.jsonl.gz'
    with gzip.open(path, 'rt') as source:
        for index, line in enumerate(source):
            obs = Observation.from_dict(json.loads(line)['observation'])
            assert rook.choose_action(obs, original_memory) == fast.choose_action(obs, fast_memory), index
