import logging
import sys
import os


def get_logger(module_name):
    SH = logging.StreamHandler(stream=sys.stdout)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s:%(message)s")
    SH.setFormatter(fmt)
    log = logging.getLogger(module_name)
    log.addHandler(SH)
    log.setLevel(os.environ.get("LOG_LEVEL", "info").upper())
    return log

