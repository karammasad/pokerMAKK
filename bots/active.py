"""Select the strategy used by the tournament entry point."""
import importlib
import os

ACTIVE_BOT = os.environ.get("POKER_BOT", "messi_v10")


def get_bot():
    from bots.portfolio import factory as portfolio_factory, names as portfolio_names
    if ACTIVE_BOT in portfolio_names():
        module = portfolio_factory(ACTIVE_BOT)
    else:
        module = importlib.import_module(f"bots.{ACTIVE_BOT}.bot")
        load = getattr(module, "load", None)
        if load:
            load()
    from bots.common.safe import wrap
    return wrap(module)
