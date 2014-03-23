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
    def __init__(self, queue, apiToken, instrument, exchange, frequency):
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
        self.__instrument = instrument
        self.__exchange = exchange
        self.__frequency = frequency
        self.__nextDateTime = utcnow()
 
    def getNextCallDateTime(self):
        return self.__nextDateTime

    def doCall(self):
        now = utcnow()
        self.__nextDateTime = now + self.__timeDelta

        try:
            logger.debug("Requesting bars with precision %s and period %s" % (self.__precision, self.__period))
            identifierType = "Symbol"
            res = api.XigniteGlobalRealTime_GetBar(self.__apiToken, self.__instrument, identifierType, self.__exchange, now, self.__precision, self.__period)
            logger.debug(res)
        except api.XigniteError, e:
            logger.error(e)


class LiveFeed(barfeed.BaseBarFeed):

    QUEUE_TIMEOUT = 0.01

    # apiToken
    # instrument
    # exchange: Market identification code (ARCX, CHIX, OOTC, PINX, XASE, XNAS, XNYS, XOTC)
    def __init__(self, apiToken, instrument, exchange, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
        barfeed.BaseBarFeed.__init__(self, frequency, maxLen)
        self.__queue = Queue.Queue()
        self.__thread = GetBarThread(self.__queue, apiToken, instrument, exchange, frequency)

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
        # Return the datetime for the next event.
        # This is needed to properly synchronize non-realtime subjects.
        return None
        raise NotImplementedError()

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
            eventType, eventData = self.__client.getQueue().get(True, Feed.QUEUE_TIMEOUT)
            if eventType == GetBarsThread.ON_BARS:
                pass
            else:
                logger.error("Invalid event received: %s - %s" % (eventType, eventData))
        except Queue.Empty:
            pass
        return ret
