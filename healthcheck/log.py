
import logging
import sys


def getLogger(name="healthcheck"):
    formatter = logging.Formatter("%(asctime)s - %(name)-20s - %(levelname)-7s   %(message)s")
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    if sys.stdout.isatty():
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.ERROR)

    logger.addHandler(ch)

    return logger





