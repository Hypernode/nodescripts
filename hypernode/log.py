
import logging
import logging.handlers
import sys


def getLogger(name="hypernode"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger


class MyBufferHandler(logging.handlers.BufferingHandler):
    """
    This is our implementation of the logging BufferingHandler that
    never removes any records. It has overridden flush() and shouldFlush()
    methods.

    Should you ever want to clear the logs, use truncate().

    Also see nosetests.logcapture.MyMemoryHandler.
    """
    def __init__(self, capacity=1000):
        logging.handlers.BufferingHandler.__init__(self, capacity)

    def flush(self):
        pass

    def truncate(self):
        self.buffer = []

    def shouldFlush(self, record):
        return False

    def formatBuffer(self):
        return [self.format(x) for x in self.buffer]


def attachBufferHandler(logger):
    formatter = logging.Formatter("%(asctime)s - %(name)-20s - %(levelname)-7s   %(message)s")
    bh = MyBufferHandler()
    bh.setFormatter(formatter)
    bh.setLevel(logging.DEBUG)
    logger.addHandler(bh)
    return bh


def attachConsoleHandler(logger):
    formatter = logging.Formatter("%(asctime)s - %(name)-20s - %(levelname)-7s   %(message)s")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)
    return ch


def attachSyslogHandler(logger):
    formatter = logging.Formatter('%(name)s: %(levelname)s %(message)s')
    syslog = logging.handlers.SysLogHandler(address='/dev/log')
    syslog.setFormatter(formatter)
    syslog.setLevel(logging.INFO)
    logger.addHandler(syslog)
    return syslog