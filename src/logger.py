import logging

logger = logging.getLogger("script_logger")
logger.setLevel(logging.DEBUG)

fmtstr = "%(asctime)s %(module)s [%(levelname)s] > %(funcName)s: %(message)s"
fmtdate = "%H:%M:%S"
fmter = logging.Formatter(fmtstr, fmtdate)

ch = logging.StreamHandler()
ch.setFormatter(fmter)
logger.addHandler(ch)
