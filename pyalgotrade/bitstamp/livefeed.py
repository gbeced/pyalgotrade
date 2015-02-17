# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import datetime
import time
import Queue

from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade import barfeed
from pyalgotrade import observer
from pyalgotrade.bitstamp import common
from pyalgotrade.bitstamp import wsclient


class TradeBar(bar.Bar):
    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__tradeId', '__price', '__amount')

    def __init__(self, dateTime, trade):
        self.__dateTime = dateTime
        self.__tradeId = trade.getId()
        self.__price = trade.getPrice()
        self.__amount = trade.getAmount()

    def __setstate__(self, state):
        (self.__dateTime, self.__tradeId, self.__price, self.__amount) = state

    def __getstate__(self):
        return (self.__dateTime, self.__tradeId, self.__price, self.__amount)

    def setUseAdjustedValue(self, useAdjusted):
        if useAdjusted:
            raise Exception("Adjusted close is not available")

    def getTradeId(self):
        return self.__tradeId

    def getFrequency(self):
        return bar.Frequency.TRADE

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        return self.__price

    def getHigh(self, adjusted=False):
        return self.__price

    def getLow(self, adjusted=False):
        return self.__price

    def getClose(self, adjusted=False):
        return self.__price

    def getVolume(self):
        return self.__amount

    def getAdjClose(self):
        return None

    def getTypicalPrice(self):
        return self.__price

    def getPrice(self):
        return self.__price

    def getUseAdjValue(self):
        return False


class LiveTradeFeed(barfeed.BaseBarFeed):

    """A real-time BarFeed that builds bars from live trades.

    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.

    .. note::
        Note that a Bar will be created for every trade, so open, high, low and close values will all be the same.
    """

    QUEUE_TIMEOUT = 0.01

    def __init__(self, maxLen=dataseries.DEFAULT_MAX_LEN):
        if not isinstance(maxLen, int):
            raise Exception("Invalid type for maxLen parameter")

        barfeed.BaseBarFeed.__init__(self, bar.Frequency.TRADE, maxLen)
        self.__barDicts = []
        self.registerInstrument(common.btc_symbol)
        self.__prevTradeDateTime = None
        self.__thread = None
        self.__initializationOk = None
        self.__enableReconnection = True
        self.__stopped = False
        self.__orderBookUpdateEvent = observer.Event()

    # Factory method for testing purposes.
    def buildWebSocketClientThread(self):
        return wsclient.WebSocketClientThread()

    def getCurrentDateTime(self):
        return wsclient.get_current_datetime()

    def enableReconection(self, enableReconnection):
        self.__enableReconnection = enableReconnection

    def __initializeClient(self):
        self.__initializationOk = None
        common.logger.info("Initializing websocket client.")

        try:
            # Start the thread that runs the client.
            self.__thread = self.buildWebSocketClientThread()
            self.__thread.start()
        except Exception, e:
            self.__initializationOk = False
            common.logger.error("Error connecting : %s" % str(e))

        # Wait for initialization to complete.
        while self.__initializationOk is None and self.__thread.is_alive():
            self.__dispatchImpl([wsclient.WebSocketClient.ON_CONNECTED])

        if self.__initializationOk:
            common.logger.info("Initialization ok.")
        else:
            common.logger.error("Initialization failed.")
        return self.__initializationOk

    def __onConnected(self):
        self.__initializationOk = True

    def __onDisconnected(self):
        if self.__enableReconnection:
            initialized = False
            while not self.__stopped and not initialized:
                common.logger.info("Reconnecting")
                initialized = self.__initializeClient()
                if not initialized:
                    time.sleep(5)
        else:
            self.__stopped = True

    def __dispatchImpl(self, eventFilter):
        ret = False
        try:
            eventType, eventData = self.__thread.getQueue().get(True, LiveTradeFeed.QUEUE_TIMEOUT)
            if eventFilter is not None and eventType not in eventFilter:
                return False

            ret = True
            if eventType == wsclient.WebSocketClient.ON_TRADE:
                self.__onTrade(eventData)
            elif eventType == wsclient.WebSocketClient.ON_ORDER_BOOK_UPDATE:
                self.__orderBookUpdateEvent.emit(eventData)
            elif eventType == wsclient.WebSocketClient.ON_CONNECTED:
                self.__onConnected()
            elif eventType == wsclient.WebSocketClient.ON_DISCONNECTED:
                self.__onDisconnected()
            else:
                ret = False
                common.logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
        except Queue.Empty:
            pass
        return ret

    # Bar datetimes should not duplicate. In case trade object datetimes conflict, we just move one slightly forward.
    def __getTradeDateTime(self, trade):
        ret = trade.getDateTime()
        if ret == self.__prevTradeDateTime:
            ret += datetime.timedelta(microseconds=1)
        self.__prevTradeDateTime = ret
        return ret

    def __onTrade(self, trade):
        # Build a bar for each trade.
        barDict = {
            common.btc_symbol: TradeBar(self.__getTradeDateTime(trade), trade)
            }
        self.__barDicts.append(barDict)

    def barsHaveAdjClose(self):
        return False

    def getNextBars(self):
        ret = None
        if len(self.__barDicts):
            ret = bar.Bars(self.__barDicts.pop(0))
        return ret

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # This may raise.
    def start(self):
        if self.__thread is not None:
            raise Exception("Already running")
        elif not self.__initializeClient():
            self.__stopped = True
            raise Exception("Initialization failed")

    def dispatch(self):
        # Note that we may return True even if we didn't dispatch any Bar
        # event.
        ret = False
        if self.__dispatchImpl(None):
            ret = True
        if barfeed.BaseBarFeed.dispatch(self):
            ret = True
        return ret

    # This should not raise.
    def stop(self):
        try:
            self.__stopped = True
            if self.__thread is not None and self.__thread.is_alive():
                common.logger.info("Shutting down websocket client.")
                self.__thread.stop()
        except Exception, e:
            common.logger.error("Error shutting down client: %s" % (str(e)))

    # This should not raise.
    def join(self):
        if self.__thread is not None:
            self.__thread.join()

    def eof(self):
        return self.__stopped

    def getOrderBookUpdateEvent(self):
        """Returns the event that will be emitted as new trades are received from Bitstamp.
        To subscribe to this event you need to pass in a callable object that receives one parameter:

        1. A :class:`pyalgotrade.bitstamp.wsclient.OrderBookUpdate` instance.
        """
        return self.__orderBookUpdateEvent
