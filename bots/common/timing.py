"""Per-half timing bookkeeping shared by safety wrappers and league reports."""
import time


def start():
    return time.perf_counter()


def elapsed_ms(mark):
    return (time.perf_counter() - mark) * 1000.0


def record(memory, seconds):
    memory["_think_s"] = memory.get("_think_s", 0.0) + seconds
    memory.setdefault("_decision_ms", []).append(seconds * 1000.0)
    return memory["_think_s"]
