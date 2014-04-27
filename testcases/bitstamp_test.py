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

import unittest
import datetime
import json

from pyalgotrade.bitstamp import barfeed
from pyalgotrade.bitstamp import broker
from pyalgotrade.bitstamp import wsclient
from pyalgotrade import observer
from pyalgotrade import strategy


class MockClient(observer.Subject):
    def __init__(self):
        self.__tradeEvent = observer.Event()
        self.__orderBookUpdateEvent = observer.Event()
        self.__events = []

    # This may raise.
    def start(self):
        pass

    # This should not raise.
    def stop(self):
        pass

    # This should not raise.
    def join(self):
        pass

    # Return True if there are not more events to dispatch.
    def eof(self):
        return len(self.__events) == 0

    # Dispatch events. If True is returned, it means that at least one event was dispatched.
    def dispatch(self):
        if len(self.__events):
            event = self.__events.pop(0)
            if isinstance(event, wsclient.Trade):
                self.__tradeEvent.emit(event)
            elif isinstance(event, wsclient.OrderBookUpdate):
                self.__orderBookUpdateEvent.emit(event)
            else:
                assert(False)

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    def getTradeEvent(self):
        return self.__tradeEvent

    def getOrderBookUpdateEvent(self):
        return self.__orderBookUpdateEvent

    def addTrade(self, dateTime, tid, price, amount):
        dataDict = {
            "id": tid,
            "price": price,
            "amount": amount
            }
        eventDict = {}
        eventDict["data"] = json.dumps(dataDict)
        self.__events.append(wsclient.Trade(dateTime, eventDict))


class TestStrategy(strategy.BaseStrategy):
    def __init__(self, cli, feed, brk):
        strategy.BaseStrategy.__init__(self, feed, brk)
        self.bid = None
        self.ask = None
        self.posExecutionInfo = []

        # Subscribe to order book update events to get bid/ask prices to trade.
        cli.getOrderBookUpdateEvent().subscribe(self.__onOrderBookUpdate)

    def __onOrderBookUpdate(self, orderBookUpdate):
        bid = orderBookUpdate.getBidPrices()[0]
        ask = orderBookUpdate.getAskPrices()[0]

        if bid != self.bid or ask != self.ask:
            self.bid = bid
            self.ask = ask

    def onEnterOk(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onEnterCanceled(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onExitOk(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())

    def onExitCanceled(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())


class TestCase(unittest.TestCase):
    def testInstrumentTraits(self):
        traits = broker.BTCTraits()
        self.assertEqual(traits.roundQuantity(0), 0)
        self.assertEqual(traits.roundQuantity(1), 1)
        self.assertEqual(traits.roundQuantity(1.1 + 1.1 + 1.1), 3.3)
        self.assertEqual(traits.roundQuantity(1.1 + 1.1 + 1.1 - 3.3), 0)
        self.assertEqual(traits.roundQuantity(0.00441376), 0.00441376)
        self.assertEqual(traits.roundQuantity(0.004413764), 0.00441376)

    def testBuyWithPartialFill(self):

        class Strategy(TestStrategy):
            def __init__(self, cli, feed, brk):
                TestStrategy.__init__(self, cli, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)

        cli = MockClient()
        cli.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        cli.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)

        barFeed = barfeed.LiveTradeFeed(cli)
        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(cli, barFeed, brk)

        strat.getDispatcher().addSubject(cli)
        strat.run()

        self.assertTrue(strat.pos.isOpen())
        self.assertEqual(round(strat.pos.getShares(), 3), 0.3)
        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill1(self):

        class Strategy(TestStrategy):
            def __init__(self, cli, feed, brk):
                TestStrategy.__init__(self, cli, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exit(limitPrice=101)

        cli = MockClient()
        cli.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        cli.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
        cli.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
        cli.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)

        barFeed = barfeed.LiveTradeFeed(cli)
        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(cli, barFeed, brk)

        strat.getDispatcher().addSubject(cli)
        strat.run()

        self.assertTrue(strat.pos.isOpen())
        self.assertEqual(round(strat.pos.getShares(), 3), 0.1)
        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testBuyAndSellWithPartialFill2(self):

        class Strategy(TestStrategy):
            def __init__(self, cli, feed, brk):
                TestStrategy.__init__(self, cli, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 1, True)
                elif bars.getDateTime() == datetime.datetime(2000, 1, 3):
                    self.pos.exit(limitPrice=101)

        cli = MockClient()
        cli.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
        cli.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
        cli.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
        cli.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)
        cli.addTrade(datetime.datetime(2000, 1, 6), 1, 102, 5)

        barFeed = barfeed.LiveTradeFeed(cli)
        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(cli, barFeed, brk)

        strat.getDispatcher().addSubject(cli)
        strat.run()

        self.assertFalse(strat.pos.isOpen())
        self.assertEqual(strat.pos.getShares(), 0)
        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

    def testRoundingBugWithTrades(self):
        # Unless proper rounding is in place 0.01 - 0.00441376 - 0.00445547 - 0.00113077 == 6.50521303491e-19
        # instead of 0.

        class Strategy(TestStrategy):
            def __init__(self, cli, feed, brk):
                TestStrategy.__init__(self, cli, feed, brk)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLongLimit("BTC", 100, 0.01, True)
                elif self.pos.entryFilled() and not self.pos.getExitOrder():
                    self.pos.exitLimit(100, True)

        cli = MockClient()
        cli.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 1)
        cli.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.01)
        cli.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.00441376)
        cli.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.00445547)
        cli.addTrade(datetime.datetime(2000, 1, 5), 1, 100, 0.00113077)

        barFeed = barfeed.LiveTradeFeed(cli)
        brk = broker.PaperTradingBroker(1000, barFeed)
        strat = Strategy(cli, barFeed, brk)

        strat.getDispatcher().addSubject(cli)
        strat.run()

        self.assertEqual(brk.getShares("BTC"), 0)
        self.assertEqual(strat.pos.getEntryOrder().getAvgFillPrice(), 100)
        self.assertEqual(strat.pos.getExitOrder().getAvgFillPrice(), 100)
        self.assertEqual(strat.pos.getEntryOrder().getFilled(), 0.01)
        self.assertEqual(strat.pos.getExitOrder().getFilled(), 0.01)
        self.assertEqual(strat.pos.getEntryOrder().getRemaining(), 0)
        self.assertEqual(strat.pos.getExitOrder().getRemaining(), 0)
        self.assertEqual(strat.pos.getEntryOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())
        self.assertEqual(strat.pos.getExitOrder().getSubmitDateTime().date(), wsclient.get_current_datetime().date())

        self.assertFalse(strat.pos.isOpen())
        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.pos.getShares(), 0.0)
