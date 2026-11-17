import logging
import os

ROOT_LOGGER_NAME = "supabase"
LOG_LEVEL_VARIABLE = "SUPABASE_LOG"

_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}


def _configure_root_logger() -> None:
    root = logging.getLogger(ROOT_LOGGER_NAME)
    root.addHandler(logging.NullHandler())
    level = _LEVELS.get(os.environ.get(LOG_LEVEL_VARIABLE, "").strip().lower())
    if level is None:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root.addHandler(handler)
    root.setLevel(level)


_configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """The logger `supabase.<name>`, part of the hierarchy every Supabase
    package logs under."""
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
