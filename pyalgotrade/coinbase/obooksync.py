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

import bintrees
import itertools


class PriceLevel(object):
    def __init__(self, price):
        self.__price = price
        self.__size = 0.0

    def getPrice(self):
        return self.__price

    def getSize(self):
        return round(self.__size, 8)

    def add(self, size):
        assert size > 0
        self.__size = self.__size + size
        assert round(self.__size, 8) >= 0

    def remove(self, size):
        assert size > 0
        self.__size = self.__size - size
        assert round(self.__size, 8) >= 0

    def isEmpty(self):
        return round(self.__size, 8) == 0.0


class PriceLevelList(object):
    def __init__(self, ascOrder):
        self.__ascOrder = ascOrder
        self.__values = bintrees.FastRBTree()

    def addFromOrderBookLevels(self, orderBookLevels):
        for orderBookLevel in orderBookLevels:
            self.add(orderBookLevel.getPrice(), orderBookLevel.getSize())

    def add(self, price, size):
        level = self.__values.set_default(price, PriceLevel(price))
        level.add(size)

    def remove(self, price, size):
        level = self.__values.get(price)
        assert level is not None, "No price level for %s" % (price)
        level.remove(size)
        if level.isEmpty():
            self.__values.discard(price)

    def getValues(self, maxValues=20):
        """
        Returns a list of sorted PriceLevel instances.
        """
        assert maxValues >= 0
        return list(itertools.islice(self.__values.values(self.__ascOrder == False), maxValues))


# https://docs.gdax.com/#the-code-classprettyprintmatchescode-channel
class L3OrderBookSync(object):
    def __init__(self, orderBook):
        """
        This class is responsible for mantaining a L3 order book based on order events.
        :param orderBook:
        """
        self.__lastSequenceNr = orderBook.getSequence()
        self.__bids = PriceLevelList(False)
        self.__asks = PriceLevelList(True)
        self.__bids.addFromOrderBookLevels(orderBook.getBids())
        self.__asks.addFromOrderBookLevels(orderBook.getAsks())
        self.__inOrderBook = bintrees.FastRBTree()

        # Load order ids.
        for side in ["bids", "asks"]:
            for order_info in orderBook.getDict()[side]:
                order_id = order_info[2]
                self.__inOrderBook.set_default(order_id, True)

    def __checkMsgSequence(self, msg):
        ret = False
        if msg.getSequence() > self.__lastSequenceNr:
            assert msg.getSequence() - 1 == self.__lastSequenceNr
            self.__lastSequenceNr = msg.getSequence()
            ret = True
        return ret

    def __getList(self, side):
        assert side in ["buy", "sell"]
        if side == "buy":
            return self.__bids
        else:
            return self.__asks

    def getSequence(self):
        return self.__lastSequenceNr

    def getBids(self):
        return self.__bids

    def getAsks(self):
        return self.__asks

    def onOrderReceived(self, msg):
        # The received message does not indicate a resting order on the order book.
        # It simply indicates a new incoming order which as been accepted by the matching engine for processing.
        self.__checkMsgSequence(msg)

    def onOrderOpen(self, msg):
        ret = False
        if self.__checkMsgSequence(msg):
            self.__inOrderBook.set_default(msg.getOrderId(), True)

            size = msg.getRemainingSize()
            price = msg.getPrice()
            self.__getList(msg.getSide()).add(price, size)
            ret = True
        return ret

    def onOrderDone(self, msg):
        ret = False
        if self.__checkMsgSequence(msg):
            inOrderBook = self.__inOrderBook.get(msg.getOrderId())

            if inOrderBook and msg.hasRemainingSize():
                self.__inOrderBook.discard(msg.getOrderId())
                size = msg.getRemainingSize()
                price = msg.getPrice()
                self.__getList(msg.getSide()).remove(price, size)
                ret = True
        return ret

    def onOrderMatch(self, msg):
        ret = False
        if self.__checkMsgSequence(msg):
            size = msg.getSize()
            price = msg.getPrice()
            self.__getList(msg.getSide()).remove(price, size)
            ret = True
        return ret

    def onOrderChange(self, msg):
        ret = False
        if self.__checkMsgSequence(msg) and self.__inOrderBook.get(msg.getOrderId()) is True:
            size = msg.getOldSize() - msg.getNewSize()
            if size > 0:
                price = msg.getPrice()
                self.__getList(msg.getSide()).remove(price, size)
                ret = True
        return ret
