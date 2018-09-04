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

import threading
from six.moves import queue
import time

from pyalgotrade import observer
from pyalgotrade import dispatchprio
import pyalgotrade.logger
from pyalgotrade.coinbase import httpclient
from pyalgotrade.coinbase import wsclient
from pyalgotrade.coinbase import obooksync


logger = pyalgotrade.logger.getLogger(__name__)


REST_API_URL = "https://api.gdax.com"
WEBSOCKET_FEED_URL = "wss://ws-feed.gdax.com"
# https://public.sandbox.exchange.coinbase.com/
SANDBOX_REST_API_URL = "https://api-public.sandbox.gdax.com"
SANDBOX_WEBSOCKET_FEED_URL = "wss://ws-feed-public.sandbox.gdax.com"


def pricelevels_to_obooklevels(priceLevels, maxValues):
    return map(
        lambda level: OrderBookLevel(level.getPrice(), level.getSize()),
        priceLevels.getValues(maxValues=maxValues)
    )


class OrderBookLevel(object):
    """An order book level."""

    def __init__(self, price, size):
        self.__price = price
        self.__size = size

    def getPrice(self):
        """Returns the price."""
        return float(self.__price)

    def getSize(self):
        """Returns the size."""
        return float(self.__size)


class L3OrderBook(object):
    """
    The order book.
    """

    def __init__(self, orderBookSync):
        self.__orderBookSync = orderBookSync

    def getSequence(self):
        return self.__orderBookSync.getSequence()

    def getBids(self, maxValues=20):
        """
        Returns the bids.

        :param maxValues: The maximum number of bids to return.
        :rtype: List of :class:`pyalgotrade.coinbase.client.OrderBookLevel` instances.
        """
        return pricelevels_to_obooklevels(self.__orderBookSync.getBids(), maxValues)

    def getAsks(self, maxValues=20):
        """
        Returns the asks.

        :param maxValues: The maximum number of asks to return.
        :rtype: List of :class:`pyalgotrade.coinbase.client.OrderBookLevel` instances.
        """
        return pricelevels_to_obooklevels(self.__orderBookSync.getAsks(), maxValues)


class Client(observer.Subject):

    """
    Interface with Coinbase exchange.

    :param productId: The id of the product to trade.
    :param wsURL: Websocket feed url.
    :param apiURL: Rest API url.
    """

    QUEUE_TIMEOUT = 0.01
    WAIT_CONNECT_POLL_FREQUENCY = 0.5
    ORDER_BOOK_EVENT_DISPATCH = {
        wsclient.WebSocketClient.Event.ORDER_MATCH: obooksync.L3OrderBookSync.onOrderMatch,
        wsclient.WebSocketClient.Event.ORDER_RECEIVED: obooksync.L3OrderBookSync.onOrderReceived,
        wsclient.WebSocketClient.Event.ORDER_OPEN: obooksync.L3OrderBookSync.onOrderOpen,
        wsclient.WebSocketClient.Event.ORDER_DONE: obooksync.L3OrderBookSync.onOrderDone,
        wsclient.WebSocketClient.Event.ORDER_CHANGE: obooksync.L3OrderBookSync.onOrderChange,
    }

    def __init__(self, productId, wsURL=WEBSOCKET_FEED_URL, apiURL=REST_API_URL):
        super(Client, self).__init__()
        self.__productId = productId
        self.__stopped = False
        self.__httpClient = httpclient.HTTPClient(apiURL)
        self.__orderEvents = observer.Event()
        self.__l3OrderBookEvents = observer.Event()
        self.__wsClientThread = None
        self.__lastSeqNr = 0
        self.__l3OBookSync = None
        self.__wsURL = wsURL

    def __connectWS(self, retry):
        while True:
            # Start the client thread and wait a couple of seconds seconds until it starts running
            self.__wsClientThread = wsclient.WebSocketClientThread(self.__productId, self.__wsURL)
            self.__wsClientThread.start()
            self.__wsClientThread.waitRunning(5)

            # While the thread is alive, wait until it gets connected.
            while self.__wsClientThread.is_alive() and not self.__wsClientThread.isConnected():
                time.sleep(Client.WAIT_CONNECT_POLL_FREQUENCY)

            # Check if the thread is not connected and we should retry.
            if self.__wsClientThread.isConnected() or not retry:
                break

    def refreshOrderBook(self):
        logger.info("Retrieving level 3 order book...")
        obook = self.__httpClient.getOrderBook(product=self.__productId, level=3)
        self.__l3OBookSync = obooksync.L3OrderBookSync(obook)
        logger.info("Finished retrieving level 3 order book")

    def __onConnected(self):
        self.refreshOrderBook()

    def __onDisconnected(self):
        logger.info("Waiting for websocket client to finish.")
        self.__wsClientThread.join()
        logger.info("Done")
        if not self.__stopped:
            self.__connectWS(True)

    def __onSeqNrMismatch(self):
        self.refreshOrderBook()

    def __onOrderEvent(self, eventType, eventData):
        self.__orderEvents.emit(eventData)

        # Update order book
        method = Client.ORDER_BOOK_EVENT_DISPATCH.get(eventType)
        assert method is not None
        updated = method(self.__l3OBookSync, eventData)
        # Emit an event if the orderbook got updated.
        if updated:
            self.__l3OrderBookEvents.emit(L3OrderBook(self.__l3OBookSync))

    def getHTTPClient(self):
        return self.__httpClient

    def getOrderEvents(self):
        return self.__orderEvents

    def getL3OrderBookEvents(self):
        """
        Returns the event that will be emitted when the L3 orderbook gets updated.

        Eventh handlers should receive one parameter:
         1. A :class:`pyalgotrade.coinbase.client.L3OrderBook` instance.

        :rtype: :class:`pyalgotrade.observer.Event`.
        """
        return self.__l3OrderBookEvents

    def start(self):
        self.__connectWS(False)
        if not self.__wsClientThread.isConnected():
            raise Exception("Failed to connect websocket client")

    def stop(self):
        try:
            if self.__wsClientThread is not None:
                self.__stopped = True
                self.__wsClientThread.stop()
        except Exception:
            logger.exception("Error stopping client thread")

    def join(self):
        if self.__wsClientThread is not None:
            self.__wsClientThread.join()

    def eof(self):
        return self.__stopped

    def dispatch(self):
        ret = False

        try:
            eventType, eventData = self.__wsClientThread.getQueue().get(True, Client.QUEUE_TIMEOUT)

            ret = True
            if eventType == wsclient.WebSocketClient.Event.CONNECTED:
                self.__onConnected()
            elif eventType == wsclient.WebSocketClient.Event.DISCONNECTED:
                self.__onDisconnected()
            elif eventType in [
                wsclient.WebSocketClient.Event.ORDER_MATCH,
                wsclient.WebSocketClient.Event.ORDER_RECEIVED,
                wsclient.WebSocketClient.Event.ORDER_OPEN,
                wsclient.WebSocketClient.Event.ORDER_DONE,
                wsclient.WebSocketClient.Event.ORDER_CHANGE
            ]:
                self.__onOrderEvent(eventType, eventData)
            elif eventType == wsclient.WebSocketClient.Event.SEQ_NR_MISMATCH:
                self.__onSeqNrMismatch()
            else:
                logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
                ret = False
        except queue.Empty:
            pass

        return ret

    def peekDateTime(self):
        return None

    def getDispatchPriority(self):
        # Dispatch events before the broker and barfeed.
        return min(dispatchprio.BROKER, dispatchprio.BAR_FEED) - 1
