import logging
import sys


class Logger:
    outstream = None

    @classmethod
    def init(cls, name=__name__, outstream=sys.stderr):
        formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setStream(outstream)
        handler.setLevel(logging.DEBUG)

        logging.basicConfig(handlers=[handler], level=logging.DEBUG)
        print(f"writing to file: {outstream.name}")
        cls.outstream = outstream

    @classmethod
    def log(cls, msg, level=logging.INFO):
        if not cls.outstream:
            cls.init()
        logging.log(level, msg)


    @classmethod
    def info(cls, msg):
        cls.log(msg, level=logging.INFO)


    @classmethod
    def debug(cls, msg):
        cls.log(msg, level=logging.DEBUG)


    @classmethod
    def warning(cls, msg):
        cls.log(msg, level=logging.WARNING)


    @classmethod
    def error(cls, msg):
        cls.log(msg, level=logging.ERROR)