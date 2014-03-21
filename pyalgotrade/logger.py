# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import logging
import threading

initLock = threading.Lock()
rootLoggerInitialized = False

log_format = "%(asctime)s %(name)s [%(levelname)s] %(message)s"
level = logging.INFO
file_log = None  # File name
console_log = True


def init_handler(handler):
    handler.setFormatter(Formatter(log_format))


def init_logger(logger):
    logger.setLevel(level)

    if file_log is not None:
        fileHandler = logging.FileHandler(file_log)
        init_handler(fileHandler)
        logger.addHandler(fileHandler)

    if console_log:
        consoleHandler = logging.StreamHandler()
        init_handler(consoleHandler)
        logger.addHandler(consoleHandler)


def initialize():
    global rootLoggerInitialized
    with initLock:
        if not rootLoggerInitialized:
            init_logger(logging.getLogger())
            rootLoggerInitialized = True


def getLogger(name=None):
    initialize()
    return logging.getLogger(name)


# This formatter provides a way to hook in formatTime.
class Formatter(logging.Formatter):
    DATETIME_HOOK = None

    def formatTime(self, record, datefmt=None):
        newDateTime = None

        if Formatter.DATETIME_HOOK is not None:
            newDateTime = Formatter.DATETIME_HOOK()

        if newDateTime is None:
            ret = logging.Formatter.formatTime(self, record, datefmt)
        else:
            ret = str(newDateTime)
        return ret
