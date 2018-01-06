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
import datetime

from pyalgotrade.coinbase import common
from pyalgotrade.coinbase import client
from pyalgotrade.coinbase import livefeed
from pyalgotrade import dispatcher


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.getIdleEvent().subscribe(self.__onIdle)

        self.client = client.Client(common.btc_usd_product_id)

        self.feed = livefeed.LiveTradeFeed(self.client)
        self.dispatcher.addSubject(self.feed)

        self.start = datetime.datetime.now()
        self.maxTestCaseDuration = datetime.timedelta(minutes=1)

    def __onIdle(self):
        if datetime.datetime.now() - self.start > self.maxTestCaseDuration:
            self.dispatcher.stop()

    def testEvents(self):
        events = {
            "obook": False,
            "bars": False,
            "orders": False,
        }

        def check_done():
            if all(events.values()):
                print "Stopping"
                self.dispatcher.stop()

        def on_orderbook_updated(orderbook):
            self.assertIsNotNone(orderbook.getSequence())
            bids = orderbook.getBids()
            asks = orderbook.getAsks()
            events["obook"] = True
            check_done()

        def on_bars(datetime, bars):
            bar = bars[common.btc_usd_product_id]
            self.assertIsNotNone(bar.getMatchMsg())
            self.assertIsNotNone(bar.getTypicalPrice())
            self.assertIsNotNone(bar.getPrice())
            self.assertFalse(bar.getUseAdjValue())
            events["bars"] = True
            check_done()

        def on_order_events(msg):
            msg.getSequence()
            events["orders"] = True
            check_done()

        self.maxTestCaseDuration = datetime.timedelta(minutes=2)
        self.feed.getNewValuesEvent().subscribe(on_bars)
        self.client.getL3OrderBookEvents().subscribe(on_orderbook_updated)
        self.client.getOrderEvents().subscribe(on_order_events)
        self.dispatcher.run()
        self.assertTrue(len(events) and all(events.values()))
