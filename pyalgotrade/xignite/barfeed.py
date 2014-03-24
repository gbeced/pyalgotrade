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

import time
import datetime
import threading
import Queue

from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade import dataseries
import pyalgotrade.logger
from pyalgotrade.utils import dt
import api


logger = pyalgotrade.logger.getLogger("xignite")


def utcnow():
    return dt.as_utc(datetime.datetime.utcnow())


class PollingThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__stopped = False

    def __wait(self):
        # Wait until getNextCallDateTime checking for cancelation every 0.5 second.
        nextCall = self.getNextCallDateTime()
        while not self.__stopped and utcnow() < nextCall:
            time.sleep(0.5)

    def stop(self):
        self.__stopped = True

    def stopped(self):
        return self.__stopped

    def run(self):
        logger.debug("Thread started.")
        while not self.__stopped:
            self.__wait()
            if not self.__stopped:
                try:
                    self.doCall()
                except Exception, e:
                    logger.critical("Unhandled exception", exc_info=e)
        logger.debug("Thread finished.")

    def getNextCallDateTime(self):
        raise NotImplementedError()

    def doCall(self):
        raise NotImplementedError()


class GetBarThread(PollingThread):

    # Events
    ON_BARS = 1

    def __init__(self, queue, apiToken, identifiers, frequency):
        PollingThread.__init__(self)

        # Map frequency to precision and period.
        if frequency < bar.Frequency.MINUTE:
            raise Exception("Frequency must be greater than or equal to bar.Frequency.MINUTE")
        elif frequency < bar.Frequency.HOUR:
            self.__precision = "Minutes"
            self.__period = frequency / bar.Frequency.MINUTE
            self.__timeDelta = datetime.timedelta(minutes=self.__period)
        elif frequency < bar.Frequency.DAY:
            self.__precision = "Hours"
            self.__period = frequency / bar.Frequency.HOUR
            self.__timeDelta = datetime.timedelta(hours=self.__period)
        else:
            raise Exception("Frequency must be less than bar.Frequency.DAY")

        self.__queue = queue
        self.__apiToken = apiToken
        self.__identifiers = identifiers
        self.__frequency = frequency
        self.__nextDateTime = utcnow()
 
    def getNextCallDateTime(self):
        return self.__nextDateTime

    def doCall(self):
        now = utcnow()
        self.__nextDateTime = now + self.__timeDelta
        identifierType = "Symbol"

        for indentifier in self.__identifiers:
            try:
                logger.debug("Requesting bars with precision %s and period %s for %s" % (self.__precision, self.__period, indentifier))
                res = api.XigniteGlobalRealTime_GetBar(self.__apiToken, indentifier, identifierType, now, self.__precision, self.__period)
                logger.debug(res)
            except api.XigniteError, e:
                logger.error(e)


class LiveFeed(barfeed.BaseBarFeed):

    QUEUE_TIMEOUT = 0.01

    # apiToken
    # identifiers: A list with the fully qualified identifier for the securities including the exchange suffix.
    # Valid exchange suffixes are (ARCX, CHIX, XASE, XNAS, XNYS)
    def __init__(self, apiToken, identifiers, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
        barfeed.BaseBarFeed.__init__(self, frequency, maxLen)
        self.__queue = Queue.Queue()
        self.__thread = GetBarThread(self.__queue, apiToken, identifiers, frequency)
        for instrument in identifiers:
            self.registerInstrument(instrument)

    ###################################################################### 
    # observer.Subject interface
    def start(self):
        if self.__thread.is_alive():
            raise Exception("Already strated")

        # Start the thread that runs the client.
        self.__thread.start()

    def stop(self):
        self.__thread.stop()

    def join(self):
        if self.__thread.is_alive():
            self.__thread.join()

    def eof(self):
        return self.__thread.stopped()

    def peekDateTime(self):
        return None

    def isRealTime(self):
        return True

    ###################################################################### 
    # barfeed.BaseBarFeed interface
    def barsHaveAdjClose(self):
        return False

    def getNextBars(self):
        return None

        ret = None
        try:
            eventType, eventData = self.__client.getQueue().get(True, LiveFeed.QUEUE_TIMEOUT)
            if eventType == GetBarThread.ON_BARS:
                pass
            else:
                logger.error("Invalid event received: %s - %s" % (eventType, eventData))
        except Queue.Empty:
            pass
        return ret
