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

import unittest
import time
import random
import json

from pyalgotrade.coinbase import obooksync
from pyalgotrade.coinbase import httpclient
from pyalgotrade.coinbase import messages
import common


class PriceLevelTestCase(unittest.TestCase):
    def testEmpty(self):
        level = obooksync.PriceLevel(1)
        self.assertTrue(level.isEmpty())
        self.assertEqual(level.getPrice(), 1)
        self.assertEqual(level.getSize(), 0)

    def testAddRemove(self):
        level = obooksync.PriceLevel(1)
        level.add(0.00000001)
        self.assertFalse(level.isEmpty())
        self.assertEqual(level.getSize(), 0.00000001)
        level.remove(0.00000001)
        self.assertTrue(level.isEmpty())
        self.assertEqual(level.getSize(), 0)

    def testRandomValues(self):
        seed = time.time()
        random.seed(seed)
        level = obooksync.PriceLevel(1)
        values = [random.randint(1, 21000000) * 1e-8 for i in range(10000)]
        for value in values:
            level.add(value)
        self.assertFalse(level.isEmpty(), "using seed %s" % (seed))
        self.assertEqual(level.getSize(), round(sum(values), 8), "using seed %s" % (seed))

        for value in values:
            level.remove(value)
        self.assertTrue(level.isEmpty(), "using seed %s" % (seed))


class PriceLevelListTestCase(unittest.TestCase):
    def testBidsOneLevel(self):
        bids = obooksync.PriceLevelList(False)

        bids.add(10, 0.11)
        bids.add(10, 0.1)
        self.assertEqual(len(bids.getValues()), 1)
        self.assertEqual(bids.getValues()[0].getPrice(), 10)
        self.assertEqual(bids.getValues()[0].getSize(), 0.21)

        bids.remove(10, 0.1)
        self.assertEqual(len(bids.getValues()), 1)
        self.assertEqual(bids.getValues()[0].getPrice(), 10)
        self.assertEqual(bids.getValues()[0].getSize(), 0.11)

        bids.remove(10, 0.11)
        self.assertEqual(len(bids.getValues()), 0)

    def testBidsManyLevels(self):
        bids = obooksync.PriceLevelList(False)
        value = 0.11

        for price in range(1, 11):
            bids.add(price, value)

        self.assertEqual(len(bids.getValues()), 10)
        self.assertEqual(bids.getValues()[0].getPrice(), 10)
        self.assertEqual(bids.getValues()[-1].getPrice(), 1)
        for level in bids.getValues():
            self.assertEqual(level.getSize(), value)

    def testAsksOneLevel(self):
        asks = obooksync.PriceLevelList(True)

        asks.add(10, 0.11)
        asks.add(10, 0.1)
        self.assertEqual(len(asks.getValues()), 1)
        self.assertEqual(asks.getValues()[0].getPrice(), 10)
        self.assertEqual(asks.getValues()[0].getSize(), 0.21)

        asks.remove(10, 0.1)
        self.assertEqual(len(asks.getValues()), 1)
        self.assertEqual(asks.getValues()[0].getPrice(), 10)
        self.assertEqual(asks.getValues()[0].getSize(), 0.11)

        asks.remove(10, 0.11)
        self.assertEqual(len(asks.getValues()), 0)

    def testAsksManyLevels(self):
        asks = obooksync.PriceLevelList(True)
        value = 0.11

        for price in range(1, 11):
            asks.add(price, value)

        self.assertEqual(len(asks.getValues()), 10)
        self.assertEqual(asks.getValues()[0].getPrice(), 1)
        self.assertEqual(asks.getValues()[-1].getPrice(), 10)
        for level in asks.getValues():
            self.assertEqual(level.getSize(), value)

    def __testRandomValuesImpl(self, ascOrder):
        seed = time.time()
        random.seed(seed)
        levelList = obooksync.PriceLevelList(ascOrder)

        prices = [random.randint(1, 10) * 1e-2 for i in range(10000)]
        values = [random.randint(1, 21000000) * 1e-8 for i in range(10000)]
        for i in range(len(prices)):
            levelList.add(prices[i], values[i])

        levels = levelList.getValues()
        if ascOrder:
            self.assertLess(levels[0].getPrice(), levels[-1].getPrice(), "using seed %s" % (seed))
            self.assertLess(levels[0].getPrice(), levels[1].getPrice(), "using seed %s" % (seed))
        else:
            self.assertGreater(levels[0].getPrice(), levels[1].getPrice(), "using seed %s" % (seed))
            self.assertGreater(levels[0].getPrice(), levels[-1].getPrice(), "using seed %s" % (seed))

        for i in range(len(prices)):
            levelList.remove(prices[i], values[i])
        self.assertEqual(len(levelList.getValues()), 0)

    def testBidsRandomValues(self):
        self.__testRandomValuesImpl(False)

    def testAsksRandomValues(self):
        self.__testRandomValuesImpl(True)

    def testInvalidRemoveFails(self):
        levelList = obooksync.PriceLevelList(True)
        with self.assertRaisesRegexp(AssertionError, "No price level for 10"):
            levelList.remove(10, 1)


class OrderBookSyncTestCase(unittest.TestCase):
    def __loadOrderBook(self, jsonFileName):
        with open(jsonFileName, "r") as f:
            return httpclient.OrderBook(json.loads(f.read()))

    def __comparePriceLevelList(self, first, second):
        maxValues = 10000
        valuesFirst = first.getValues(maxValues=maxValues)
        valuesSecond = second.getValues(maxValues=maxValues)
        self.assertEqual(len(valuesFirst), len(valuesSecond))
        for i in range(len(valuesFirst)):
            self.assertEqual(valuesFirst[i].getPrice(), valuesSecond[i].getPrice())
            self.assertEqual(valuesFirst[i].getSize(), valuesSecond[i].getSize())

    def __compareOrderBookSync(self, first, second):
        self.__comparePriceLevelList(first.getAsks(), second.getAsks())
        self.__comparePriceLevelList(first.getBids(), second.getBids())

    def testOrderBookEventsSync(self):
        # Load starting order book and replay events.
        obookSync = obooksync.OrderBookSync(self.__loadOrderBook(
            common.get_data_file_path("coinbase_obook_begin.json"))
        )
        with open(common.get_data_file_path("coinbase_messages.json"), "r") as f:
            for line in f:
                line = line.strip()
                msgDict = json.loads(line)
                msg_type = msgDict.get("type")
                if msg_type == "received":
                    obookSync.onOrderReceived(messages.Received(msgDict))
                elif msg_type == "open":
                    obookSync.onOrderOpen(messages.Open(msgDict))
                elif msg_type == "done":
                    obookSync.onOrderDone(messages.Done(msgDict))
                elif msg_type == "match":
                    obookSync.onOrderMatch(messages.Match(msgDict))
                elif msg_type == "change":
                    obookSync.onOrderChange(messages.Change(msgDict))
                else:
                    self.assertTrue(False, "Unknown message type")

        # Compare to final order book.
        expectedOBookSync = obooksync.OrderBookSync(
            self.__loadOrderBook(common.get_data_file_path("coinbase_obook_end.json"))
        )
        self.__compareOrderBookSync(obookSync, expectedOBookSync)
