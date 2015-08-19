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


# https://docs.exchange.coinbase.com/#real-time-order-book
class OrderBookSync(object):
    def __init__(self, orderBook):
        self.__lastSequenceNr = orderBook.getSequence()
        self.__bids = PriceLevelList(False)
        self.__asks = PriceLevelList(True)

    def onOrderReceived(self, msg):
        pass

    def onOrderOpen(self, msg):
        pass

    def onOrderDone(self, msg):
        pass

    def onOrderMatch(self, msg):
        pass

    def onOrderChange(self, msg):
        pass
