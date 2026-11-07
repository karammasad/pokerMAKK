"""Optional parity check between the in-process league and the real HTTP judge.

Run with: RUN_HTTP_MATCH_TESTS=1 python -m pytest -q tests/test_datathon_http.py
"""
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

import game
from bots.common.safe import wrap
from league.run import play_half
from league.zoo.simple import factory

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(os.environ.get("RUN_HTTP_MATCH_TESTS") != "1", reason="set RUN_HTTP_MATCH_TESTS=1 to launch local HTTP bots")


def free_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_for_name(port, expected, process):
    deadline = time.time() + 15
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"bot server exited ({process.returncode})")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.5) as response:
                name = json.loads(response.read()).get("agent_name")
            if name == expected:
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"{expected} did not answer on port {port}")


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_http_judge_matches_inprocess_paired_chips(tmp_path):
    agent_port, opp_port = free_port(), free_port()
    env_agent = os.environ.copy(); env_agent["PORT"] = str(agent_port); env_agent["POKER_BOT"] = "m1_equity"
    env_opp = os.environ.copy(); env_opp["PORT"] = str(opp_port)
    agent = subprocess.Popen([sys.executable, "agent.py"], cwd=ROOT, env=env_agent, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    opponent = subprocess.Popen([sys.executable, "baseline-bots/baseline_random.py"], cwd=ROOT, env=env_opp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wait_for_name(agent_port, "m1_equity", agent)
        wait_for_name(opp_port, "RandomBot", opponent)
        seed, deals = "http-parity", 16
        output = tmp_path / "judge.json"
        run = subprocess.run([sys.executable, "judge_engine.py", "--agent1", str(agent_port), "--agent2", str(opp_port),
                             "--deals", str(deals), "--seed", seed, "--json", str(output)],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, run.stdout + run.stderr
        judge = json.loads(output.read_text())
        assert all(half["errors"] == 0 for half in judge["agent_stats"]["agent1"])

        strategy = importlib.import_module("bots.m1_equity.bot")
        strategy.load()
        our_bot, zoo_bot = wrap(strategy), wrap(factory("random"))
        half_one, err_one, _ = play_half(our_bot, zoo_bot, seed, 1, deals)
        half_two, err_two, _ = play_half(our_bot, zoo_bot, seed, 2, deals)
        assert err_one == err_two == 0
        paired = [(half_one[i] + half_two[i]) / game.BIG_BLIND for i in range(deals)]
        assert paired == judge["paired_bb"]
    finally:
        stop(opponent)
        stop(agent)
