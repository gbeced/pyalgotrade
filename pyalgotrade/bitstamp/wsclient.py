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

from pyalgotrade.websocket import pusher
from pyalgotrade.websocket import client
from pyalgotrade.bitstamp import common


def get_current_datetime():
    return datetime.datetime.now()

# Bitstamp protocol reference: https://www.bitstamp.net/websocket/


class Trade(pusher.Event):
    """A trade event."""

    def __init__(self, dateTime, eventDict):
        super(Trade, self).__init__(eventDict, True)
        self.__dateTime = dateTime

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` when this event was received."""
        return self.__dateTime

    def getId(self):
        """Returns the trade id."""
        return self.getData()["id"]

    def getPrice(self):
        """Returns the trade price."""
        return self.getData()["price"]

    def getAmount(self):
        """Returns the trade amount."""
        return self.getData()["amount"]

    def isBuy(self):
        """Returns True if the trade was a buy."""
        return self.getData()["type"] == 0

    def isSell(self):
        """Returns True if the trade was a sell."""
        return self.getData()["type"] == 1


class OrderBookUpdate(pusher.Event):
    """An order book update event."""

    def __init__(self, dateTime, eventDict):
        super(OrderBookUpdate, self).__init__(eventDict, True)
        self.__dateTime = dateTime

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` when this event was received."""
        return self.__dateTime

    def getBidPrices(self):
        """Returns a list with the top 20 bid prices."""
        return [float(bid[0]) for bid in self.getData()["bids"]]

    def getBidVolumes(self):
        """Returns a list with the top 20 bid volumes."""
        return [float(bid[1]) for bid in self.getData()["bids"]]

    def getAskPrices(self):
        """Returns a list with the top 20 ask prices."""
        return [float(ask[0]) for ask in self.getData()["asks"]]

    def getAskVolumes(self):
        """Returns a list with the top 20 ask volumes."""
        return [float(ask[1]) for ask in self.getData()["asks"]]


class WebSocketClient(pusher.WebSocketClient):
    """
    This websocket client class is designed to be running in a separate thread and for that reason
    events are pushed into a queue.
    """

    PUSHER_APP_KEY = "de504dc5763aeef9ff52"

    class Event:
        TRADE = 1
        ORDER_BOOK_UPDATE = 2
        CONNECTED = 3
        DISCONNECTED = 4

    def __init__(self, queue):
        super(WebSocketClient, self).__init__(WebSocketClient.PUSHER_APP_KEY, 5)
        self.__queue = queue

    def onMessage(self, msg):
        # If we can't handle the message, forward it to Pusher WebSocketClient.
        event = msg.get("event")
        if event == "trade":
            self.onTrade(Trade(get_current_datetime(), msg))
        elif event == "data" and msg.get("channel") == "order_book":
            self.onOrderBookUpdate(OrderBookUpdate(get_current_datetime(), msg))
        else:
            super(WebSocketClient, self).onMessage(msg)

    ######################################################################
    # WebSocketClientBase events.

    def onClosed(self, code, reason):
        common.logger.info("Closed. Code: %s. Reason: %s." % (code, reason))
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    def onDisconnectionDetected(self):
        common.logger.warning("Disconnection detected.")
        try:
            self.stopClient()
        except Exception as e:
            common.logger.error("Error stopping websocket client: %s." % (str(e)))
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    ######################################################################
    # Pusher specific events.

    def onConnectionEstablished(self, event):
        common.logger.info("Connection established.")
        self.__queue.put((WebSocketClient.Event.CONNECTED, None))

        channels = ["live_trades", "order_book"]
        common.logger.info("Subscribing to channels %s." % channels)
        for channel in channels:
            self.subscribeChannel(channel)

    def onError(self, event):
        common.logger.error("Error: %s" % (event))

    def onUnknownEvent(self, event):
        common.logger.warning("Unknown event: %s" % (event))

    ######################################################################
    # Bitstamp specific

    def onTrade(self, trade):
        self.__queue.put((WebSocketClient.Event.TRADE, trade))

    def onOrderBookUpdate(self, orderBookUpdate):
        self.__queue.put((WebSocketClient.Event.ORDER_BOOK_UPDATE, orderBookUpdate))


class WebSocketClientThread(client.WebSocketClientThreadBase):
    """
    This thread class is responsible for running a WebSocketClient.
    """

    def __init__(self):
        super(WebSocketClientThread, self).__init__()
        self.__queue = queue.Queue()
        self.__wsClient = None

    def getQueue(self):
        return self.__queue

    def run(self):
        super(WebSocketClientThread, self).run()

        # We create the WebSocketClient right in the thread, instead of doing so in the constructor,
        # because it has thread affinity.
        try:
            self.__wsClient = WebSocketClient(self.__queue)
            self.__wsClient.connect()
            self.__wsClient.startClient()
        except Exception:
            common.logger.exception("Failed to connect: %s")

    def stop(self):
        try:
            if self.__wsClient is not None:
                common.logger.info("Stopping websocket client.")
                self.__wsClient.stopClient()
        except Exception as e:
            common.logger.error("Error stopping websocket client: %s." % (str(e)))
