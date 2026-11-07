"""Select the strategy used by the tournament entry point."""
import importlib

ACTIVE_BOT = "m1_equity"


def get_bot():
    module = importlib.import_module(f"bots.{ACTIVE_BOT}.bot")
    load = getattr(module, "load", None)
    if load:
        load()
    from bots.common.safe import wrap
    return wrap(module)
