import sys
from typing import *
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler


def get_logger(
        name: str, level: int,
        formatting: Optional[str] = None,
        master_file: bool = True,
        stdout: bool = False
) -> logging.Logger:
    path = Path(__file__)

    for _ in __name__.split("."):
        path = path.parent

    path = path.joinpath("logs")
    if not path.exists():
        path.mkdir()
    path = path.joinpath(f"{'main' if master_file else name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.handlers.TimedRotatingFileHandler(
        path, when="W0", backupCount=14, delay=True
    )
    handler.setFormatter(logging.Formatter(
        formatting if formatting else "%(levelname)s from '%(name)s' @ %(asctime)s: %(message)s"
    ))

    logger.addHandler(handler)

    if stdout:
        logger.addHandler(logging.StreamHandler(sys.stdout))

    return logger



