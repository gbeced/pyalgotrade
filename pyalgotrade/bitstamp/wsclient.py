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

import json

import pyalgotrade.logger
from pyalgotrade.websocket import client
from pyalgotrade.utils import dt
from pyalgotrade.bitstamp import common
from pyalgotrade.instrument import build_instrument


logger = pyalgotrade.logger.getLogger(__name__)


# Bitstamp protocol reference: https://www.bitstamp.net/websocket/v2/

class Event(object):
    def __init__(self, eventDict):
        self._eventDict = eventDict

    def __str__(self):
        return json.dumps(self._eventDict)

    def getDict(self):
        return self._eventDict

    def getData(self):
        return self._eventDict.get("data")

    def _getCurrencyPair(self, channel_prefix):
        channel = self.getDict()["channel"]
        assert channel.find(channel_prefix) == 0
        channelCurrencyPair = channel[len(channel_prefix):]
        return common.channel_to_instrument(channelCurrencyPair)


class TimestampedEvent(Event):
    def getDateTime(self):
        """Returns the :class:`datetime.datetime` when this event was generated."""
        microtimestamp = int(self.getData()["microtimestamp"])
        return dt.timestamp_to_datetime(microtimestamp / 1e6)


class Trade(TimestampedEvent):
    """A trade event."""

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

    def getCurrencyPair(self):
        return self._getCurrencyPair("live_trades_")


class OrderBookUpdate(TimestampedEvent):
    """An order book update event."""

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

    def getInstrument(self):
        """Returns the orderbook instrument."""
        return build_instrument(self._getCurrencyPair("detail_order_book_"))

    def getCurrencyPair(self):
        return self._getCurrencyPair("detail_order_book_")


class WebSocketClient(client.WebSocketClientBase):
    """
    This websocket client class is designed to be running in a separate thread and for that reason
    events are pushed into a queue.
    """

    class Event:
        DISCONNECTED = 1
        TRADE = 2
        ORDER_BOOK_UPDATE = 3

    def __init__(
            self, queue, currency_pairs, url="wss://ws.bitstamp.net/", ping_interval=15, ping_timeout=5
    ):
        super(WebSocketClient, self).__init__(url, ping_interval=ping_interval, ping_timeout=ping_timeout)
        assert len(currency_pairs), "Missing currency pairs"
        self.__queue = queue
        self.__pending_subscriptions = []

        for currency_pair in currency_pairs:
            self.__pending_subscriptions.append("detail_order_book_" + currency_pair)
            self.__pending_subscriptions.append("live_trades_" + currency_pair)

    def onOpened(self):
        for channel in self.__pending_subscriptions:
            logger.info("Subscribing to channel %s." % channel)
            self.send(json.dumps({
                "event": "bts:subscribe",
                "data": {
                    "channel": channel
                }
            }))

    def onMessage(self, message):
        message = json.loads(message)

        event = message.get("event")
        if event == "trade":
            self.onTrade(Trade(message))
        elif event == "data" and message.get("channel").find("detail_order_book_") == 0:
            self.onOrderBookUpdate(OrderBookUpdate(message))
        elif event == "bts:subscription_succeeded":
            self.__onSubscriptionSucceeded(Event(message))
        else:
            self.onUnknownEvent(Event(message))

    def onClosed(self, code, reason):
        logger.info("Closed. Code: %s. Reason: %s." % (code, reason))
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    def onError(self, exception):
        logger.error("Error: %s." % exception)

    def onUnknownEvent(self, event):
        logger.warning("Unknown event: %s." % event)

    def onTrade(self, trade):
        self.__queue.put((WebSocketClient.Event.TRADE, trade))

    def onOrderBookUpdate(self, orderBookUpdate):
        self.__queue.put((WebSocketClient.Event.ORDER_BOOK_UPDATE, orderBookUpdate))

    def __onSubscriptionSucceeded(self, event):
        channel = event.getDict().get("channel")
        self.__pending_subscriptions.remove(channel)
        if not self.__pending_subscriptions:
            self.setInitialized()


class WebSocketClientThread(client.WebSocketClientThreadBase):
    """
    This thread class is responsible for running a WebSocketClient.
    """

    def __init__(
        self, currency_pairs, url="wss://ws.bitstamp.net/", ping_interval=15, ping_timeout=5
    ):
        super(WebSocketClientThread, self).__init__(
            WebSocketClient, currency_pairs, url, ping_interval=ping_interval, ping_timeout=ping_timeout
        )
