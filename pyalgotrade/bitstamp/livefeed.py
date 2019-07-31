# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

from six.moves import queue

import pyalgotrade.logger
from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade import observer
from pyalgotrade.bitstamp import common
from pyalgotrade.bitstamp import wsclient


logger = pyalgotrade.logger.getLogger(__name__)


class TradeBar(bar.Bar):
    def __init__(self, dateTime, trade):
        self.__dateTime = dateTime
        self.__trade = trade

    def setUseAdjustedValue(self, useAdjusted):
        if useAdjusted:
            raise Exception("Adjusted close is not available")

    def getTrade(self):
        return self.__trade

    def getTradeId(self):
        return self.__trade.getId()

    def getFrequency(self):
        return bar.Frequency.TRADE

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        return self.__trade.getPrice()

    def getHigh(self, adjusted=False):
        return self.__trade.getPrice()

    def getLow(self, adjusted=False):
        return self.__trade.getPrice()

    def getClose(self, adjusted=False):
        return self.__trade.getPrice()

    def getVolume(self):
        return self.__trade.getAmount()

    def getAdjClose(self):
        return None

    def getTypicalPrice(self):
        return self.__trade.getPrice()

    def getPrice(self):
        return self.__trade.getPrice()

    def getUseAdjValue(self):
        return False

    def isBuy(self):
        return self.__trade.isBuy()

    def isSell(self):
        return not self.__trade.isBuy()


class LiveTradeFeed(barfeed.BaseBarFeed):

    """A real-time BarFeed that builds bars from live trades.

    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.

    .. note::
        Note that a Bar will be created for every trade, so open, high, low and close values will all be the same.
    """

    QUEUE_TIMEOUT = 0.01

    def __init__(self, maxLen=None):
        super(LiveTradeFeed, self).__init__(bar.Frequency.TRADE, maxLen)
        self.__barDicts = []
        currencyPair = common.BTC_USD_CURRENCY_PAIR
        self.__channels = [common.CURRENCY_PAIR_TO_CHANNEL[currencyPair]]
        self.registerInstrument(currencyPair)
        self.__thread = None
        self.__enableReconnection = True
        self.__stopped = False
        self.__orderBookUpdateEvent = observer.Event()

    # Factory method for testing purposes.
    def buildWebSocketClientThread(self):
        return wsclient.WebSocketClientThread(currency_pairs=self.__channels)

    def getCurrentDateTime(self):
        return datetime.datetime.now()

    def enableReconection(self, enableReconnection):
        self.__enableReconnection = enableReconnection

    def __initializeClient(self):
        logger.info("Initializing websocket client")

        # Start the thread that runs the client.
        self.__thread = self.buildWebSocketClientThread()
        self.__thread.start()

        logger.info("Waiting for websocket initialization to complete")
        initialized = False
        while not initialized and not self.__stopped and self.__thread.is_alive():
            initialized = self.__thread.waitInitialized(1)

        if initialized:
            logger.info("Initialization completed")
        else:
            logger.error("Initialization failed")
        return initialized

    def __onDisconnected(self):
        if self.__enableReconnection:
            logger.info("Reconnecting")
            while not self.__stopped and not self.__initializeClient():
                pass
        elif not self.__stopped:
            logger.info("Stopping")
            self.__stopped = True

    def __dispatchImpl(self, eventFilter):
        ret = False
        try:
            eventType, eventData = self.__thread.getQueue().get(True, LiveTradeFeed.QUEUE_TIMEOUT)
            if eventFilter is not None and eventType not in eventFilter:
                return False

            ret = True
            if eventType == wsclient.WebSocketClient.Event.TRADE:
                self.__onTrade(eventData)
            elif eventType == wsclient.WebSocketClient.Event.ORDER_BOOK_UPDATE:
                self.__orderBookUpdateEvent.emit(eventData)
            elif eventType == wsclient.WebSocketClient.Event.DISCONNECTED:
                self.__onDisconnected()
            else:
                ret = False
                logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
        except queue.Empty:
            pass
        return ret

    def __onTrade(self, trade):
        assert trade.getCurrencyPair() == common.BTC_USD_CURRENCY_PAIR
        # Build a bar for each trade.
        barDict = {
            trade.getCurrencyPair(): TradeBar(trade.getDateTime(), trade)
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
        super(LiveTradeFeed, self).start()
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
        if super(LiveTradeFeed, self).dispatch():
            ret = True
        return ret

    # This should not raise.
    def stop(self):
        try:
            self.__stopped = True
            if self.__thread is not None and self.__thread.is_alive():
                logger.info("Stopping websocket client.")
                self.__thread.stop()
        except Exception as e:
            logger.error("Error shutting down client: %s" % (str(e)))

    # This should not raise.
    def join(self):
        if self.__thread is not None:
            self.__thread.join()

    def eof(self):
        return self.__stopped

    def getOrderBookUpdateEvent(self):
        """
        Returns the event that will be emitted when the orderbook gets updated.

        Eventh handlers should receive one parameter:
         1. A :class:`pyalgotrade.bitstamp.wsclient.OrderBookUpdate` instance.

        :rtype: :class:`pyalgotrade.observer.Event`.
        """
        return self.__orderBookUpdateEvent
