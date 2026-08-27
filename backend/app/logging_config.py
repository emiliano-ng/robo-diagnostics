import logging
import sys


def configure_logging() -> None:
    """Structured-ish logging to stdout — readable locally, and the format
    (timestamp, level, logger name, message) is what you'd grep/filter on
    if this were shipped to a log aggregator later.

    Deliberately not using print(): print() bypasses log levels, can't be
    filtered/redirected independently of stdout, and doesn't carry a
    timestamp or source module — none of which you want in anything beyond
    a throwaway script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )
    # SQLAlchemy's own logger is chatty at INFO (echoes every query) —
    # keep it at WARNING so app logs aren't drowned out.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
