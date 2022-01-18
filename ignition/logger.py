from typing import *
from pathlib import Path
import logging


def get_logger(name: str, level: int, formatting: Optional[str] = None, master_file: bool = False):
    path = Path(__file__)

    for _ in __name__.split("."):
        path = path.parent

    path = path.joinpath("logs")
    if not path.exists():
        path.mkdir()
    path = path.joinpath(f"{'main' if master_file else name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler(path)
    if formatting:
        handler.setFormatter(logging.Formatter(formatting))

    logger.addHandler(handler)
