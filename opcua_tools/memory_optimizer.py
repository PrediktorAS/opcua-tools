"""
Call the memory optimizer in order to minimize possible pandas' memory leaks.
Works for Linux. Does not change anything for MacOS.
"""

import logging
from ctypes import CDLL, cdll

import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


__old_pandas_del = getattr(pd.DataFrame, "__del__", None)

try:
    cdll.LoadLibrary("libc.so.6")
    libc = CDLL("libc.so.6")
    libc.malloc_trim(0)
except (OSError, AttributeError):
    libc = None


def __malloc_trim_del(self):
    if __old_pandas_del:
        __old_pandas_del(self)
    libc.malloc_trim(0)


def replace_default_pandas_del_method():
    if libc:
        logger.info("Applying memory optimizer for pd.DataFrame.__del__")
        pd.DataFrame.__del__ = __malloc_trim_del
    else:
        logger.info("Memory optimizer not applied: libc or malloc_trim() not found")
