# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
import common
import strategy_test


def load_daily_barfeed(instrument):
    barFeed = yahoofeed.Feed()
    barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
    return barFeed


class TestStrategy(strategy.BacktestingStrategy):
    def __init__(self, barFeed, instrument):
        strategy.BacktestingStrategy.__init__(self, barFeed)
        self.instrument = instrument
        self.enterOk = 0
        self.enterCanceled = 0
        self.exitOk = 0
        self.exitCanceled = 0
        self.orderUpdated = 0

    def onOrderUpdated(self, order):
        self.orderUpdated += 1

    def onEnterOk(self, position):
        self.enterOk += 1

    def onEnterCanceled(self, position):
        self.enterCanceled += 1

    def onExitOk(self, position):
        self.exitOk += 1

    def onExitCanceled(self, position):
        self.exitCanceled += 1


class EnterAndExitStrategy(TestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif self.position.entryFilled() and not self.position.exitFilled():
            self.position.exit()


class DoubleExitStrategy(TestStrategy):
    def onStart(self):
        self.position = None
        self.doubleExit = False
        self.doubleExitFailed = False

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif not self.doubleExit:
            self.doubleExit = True
            self.position.exit()
            try:
                self.position.exit()
            except Exception:
                self.doubleExitFailed = True


class CancelEntryStrategy(TestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
            self.position.cancelEntry()


class ExitEntryNotFilledStrategy(TestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
            self.position.exit()


class ResubmitExitStrategy(TestStrategy):
    def onStart(self):
        self.position = None
        self.exitRequestCanceled = False

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif self.position.entryFilled() and not self.position.exitFilled():
            self.position.exit()
            if not self.exitRequestCanceled:
                self.position.cancelExit()
                self.exitRequestCanceled = True


class TestCase(unittest.TestCase):
    TestInstrument = "doesntmatter"

    def testEnterAndExit(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = EnterAndExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.enterOk, 1)
        self.assertEqual(strat.enterCanceled, 0)
        self.assertEqual(strat.exitOk, 1)
        self.assertEqual(strat.exitCanceled, 0)
        self.assertEqual(strat.orderUpdated, 0)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)

    def testCancelEntry(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = CancelEntryStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.enterOk, 0)
        self.assertEqual(strat.enterCanceled, 1)
        self.assertEqual(strat.exitOk, 0)
        self.assertEqual(strat.exitCanceled, 0)
        self.assertEqual(strat.orderUpdated, 0)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)

    def testExitEntryNotFilled(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = ExitEntryNotFilledStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.enterOk, 0)
        self.assertEqual(strat.enterCanceled, 1)
        self.assertEqual(strat.exitOk, 0)
        self.assertEqual(strat.exitCanceled, 0)
        self.assertEqual(strat.orderUpdated, 0)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)

    def testDoubleExitFails(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = DoubleExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.enterOk, 1)
        self.assertEqual(strat.enterCanceled, 0)
        self.assertEqual(strat.exitOk, 1)
        self.assertEqual(strat.exitCanceled, 0)
        self.assertEqual(strat.orderUpdated, 0)
        self.assertEqual(strat.doubleExit, True)
        self.assertEqual(strat.doubleExitFailed, True)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)

    def testResubmitExit(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = ResubmitExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.enterOk, 1)
        self.assertEqual(strat.enterCanceled, 0)
        self.assertEqual(strat.exitOk, 1)
        self.assertEqual(strat.exitCanceled, 1)
        self.assertEqual(strat.orderUpdated, 0)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)

    def testUnrealized(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = strategy_test.TestStrategy(barFeed, 1000)
        strat.addPosEntry(datetime.date(2000, 12, 13), strat.enterLong, instrument, 1, False)  # Filled on 2000-12-14 at 29.25.
        strat.run()

        self.assertEqual(strat.getActivePosition().getUnrealizedNetProfit(), 29.06 - 29.25)
        self.assertEqual(strat.getActivePosition().getUnrealizedReturn(), (29.06 - 29.25) / 29.25)

    def testUnrealizedAdjusted(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = strategy_test.TestStrategy(barFeed, 1000)
        strat.setUseAdjustedValues(True)
        strat.addPosEntry(datetime.date(2000, 12, 13), strat.enterLong, instrument, 1, False)  # Filled on 2000-12-14 at 28.60
        strat.run()

        self.assertEqual(round(strat.getActivePosition().getUnrealizedNetProfit(), 2), round(28.41 - 28.60, 2))
        self.assertEqual(round(strat.getActivePosition().getUnrealizedReturn(), 2), round((28.41 - 28.60) / 28.60, 2))

    def testInvalidUnrealized(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = strategy_test.TestStrategy(barFeed, 1000)
        strat.addPosEntry(datetime.date(2000, 12, 13), strat.enterLong, instrument, 1, False)  # Filled on 2000-12-14 at 29.25.
        strat.addPosExit(datetime.date(2000, 12, 19))
        strat.run()

        with self.assertRaises(Exception):
            strat.getActivePosition().getUnrealizedNetProfit()

        with self.assertRaises(Exception):
            strat.getActivePosition().getUnrealizedReturn()

    def testActiveOrdersAndSharesLong(self):
        instrument = "orcl"
        testCase = self

        class Strategy(strategy.BacktestingStrategy):
            def __init__(self, barFeed, cash):
                strategy.BacktestingStrategy.__init__(self, barFeed, cash)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLong(instrument, 1, True)
                    # The entry order should be active.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 0)
                elif self.pos.isOpen():
                    # At this point the entry order should have been filled.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 1)
                    self.pos.exit()
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 1)
                else:
                    # The position was closed.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 0)

        barFeed = load_daily_barfeed(instrument)
        strat = Strategy(barFeed, 1000)
        strat.run()

        self.assertNotEqual(strat.pos, None)
        self.assertEqual(strat.pos.isOpen(), False)
        # Entered on 2000-01-04 at 115.50
        # Exit on 2000-01-05 at 101.62
        self.assertEqual(strat.pos.getNetProfit(),  101.62 - 115.50)

    def testActiveOrdersAndSharesShort(self):
        instrument = "orcl"
        testCase = self

        class Strategy(strategy.BacktestingStrategy):
            def __init__(self, barFeed, cash):
                strategy.BacktestingStrategy.__init__(self, barFeed, cash)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterShort(instrument, 1, True)
                    # The entry order should be active.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 0)
                elif self.pos.isOpen():
                    # At this point the entry order should have been filled.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), -1)
                    self.pos.exit()
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), -1)
                else:
                    # The position was closed.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 0)

        barFeed = load_daily_barfeed(instrument)
        strat = Strategy(barFeed, 1000)
        strat.run()

        self.assertNotEqual(strat.pos, None)
        self.assertEqual(strat.pos.isOpen(), False)
        # Entered on 2000-01-04 at 115.50
        # Exit on 2000-01-05 at 101.62
        self.assertEqual(strat.pos.getNetProfit(),  115.50 - 101.62)
