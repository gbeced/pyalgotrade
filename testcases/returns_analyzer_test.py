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

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.stratanalyzer import returns
from pyalgotrade import broker
from pyalgotrade import marketsession

import strategy_test
import position_test
import common

import unittest
import datetime


class TimeWeightedReturnsTestCase(unittest.TestCase):
    def testNullPortfolio(self):
        retTracker = returns.TimeWeightedReturns(0)
        self.assertEqual(retTracker.getReturn(), 0)

    def testNoUpdates(self):
        retTracker = returns.TimeWeightedReturns(10)
        self.assertEqual(retTracker.getReturn(), 0)

    def testWikiInvest(self):
        # http://www.wikinvest.com/wiki/Time-weighted_return
        retTracker = returns.TimeWeightedReturns(1000)
        retTracker.deposit(250)
        retTracker.update(1300)
        self.assertEqual(round(retTracker.getSubPeriodReturns()[-1], 2), 0.05)
        retTracker.deposit(250)
        retTracker.update(1700)
        self.assertEqual(round(retTracker.getSubPeriodReturns()[-1], 3), 0.115)
        retTracker.update(1900)
        self.assertEqual(round(retTracker.getSubPeriodReturns()[-1], 3), 0.118)
        self.assertEqual(round(retTracker.getReturn(), 4), 0.0939)


class ReturnsTrackerTestCase(unittest.TestCase):
    def testNoValues(self):
        retTracker = returns.ReturnsTracker(10)
        self.assertEqual(retTracker.getCumulativeReturn(), 0)
        self.assertEqual(retTracker.getNetReturn(), 0)
        self.assertEqual(retTracker.getCumulativeReturn(10), 0)
        self.assertEqual(retTracker.getNetReturn(10), 0)

    def testOneValue(self):
        retTracker = returns.ReturnsTracker(10)
        retTracker.updateValue(10)
        self.assertEqual(retTracker.getCumulativeReturn(), 0)
        self.assertEqual(retTracker.getNetReturn(), 0)
        self.assertEqual(retTracker.getCumulativeReturn(10), 0)
        self.assertEqual(retTracker.getNetReturn(10), 0)
        self.assertEqual(round(retTracker.getCumulativeReturn(11), 2), 0.1)
        self.assertEqual(round(retTracker.getNetReturn(11), 2), 0.1)

    def testManyValues(self):
        retTracker = returns.ReturnsTracker(10)

        retTracker.updateValue(10)
        self.assertEqual(retTracker.getCumulativeReturn(), 0)
        self.assertEqual(retTracker.getNetReturn(), 0)

        retTracker.updateValue(11)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), 0.1)
        self.assertEqual(round(retTracker.getNetReturn(), 2), 0.1)

        self.assertEqual(round(retTracker.getCumulativeReturn(11), 2), 0.1)
        self.assertEqual(round(retTracker.getNetReturn(11), 2), 0)
        retTracker.updateValue(11)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), 0.1)
        self.assertEqual(round(retTracker.getNetReturn(), 2), 0)

        self.assertEqual(round(retTracker.getCumulativeReturn(12), 2), 0.2)
        self.assertEqual(round(retTracker.getNetReturn(12), 2), 0.09)
        retTracker.updateValue(12)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), 0.2)
        self.assertEqual(round(retTracker.getNetReturn(), 2), 0.09)

        self.assertEqual(round(retTracker.getCumulativeReturn(10), 2), 0)
        self.assertEqual(round(retTracker.getNetReturn(10), 2), -0.17)
        retTracker.updateValue(10)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), 0)
        self.assertEqual(round(retTracker.getNetReturn(), 2), -0.17)

        self.assertEqual(round(retTracker.getCumulativeReturn(5), 2), -0.5)
        self.assertEqual(round(retTracker.getNetReturn(5), 2), -0.5)
        retTracker.updateValue(5)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), -0.5)
        self.assertEqual(round(retTracker.getNetReturn(), 2), -0.5)

        self.assertEqual(round(retTracker.getCumulativeReturn(6), 2), -0.4)
        self.assertEqual(round(retTracker.getNetReturn(6), 2), 0.2)
        retTracker.updateValue(6)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), -0.4)
        self.assertEqual(round(retTracker.getNetReturn(), 2), 0.2)

        self.assertEqual(round(retTracker.getCumulativeReturn(10), 2), 0)
        self.assertEqual(round(retTracker.getNetReturn(10), 2), 0.67)
        retTracker.updateValue(10)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), 0)
        self.assertEqual(round(retTracker.getNetReturn(), 2), 0.67)

    def testBankrupt(self):
        retTracker = returns.ReturnsTracker(10)
        retTracker.updateValue(5)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), -0.5)
        self.assertEqual(round(retTracker.getNetReturn(), 2), -0.5)
        retTracker.updateValue(1)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), -0.9)
        self.assertEqual(round(retTracker.getNetReturn(), 2), -0.8)
        retTracker.updateValue(0)
        self.assertEqual(round(retTracker.getCumulativeReturn(), 2), -1)
        self.assertEqual(round(retTracker.getNetReturn(), 2), -1)


class PosTrackerTestCase(unittest.TestCase):

    def testBuyAndSellBreakEven(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getCash(), 0)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getReturn(), 0)

    def testBuyAndSellBreakEvenWithCommission(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        self.assertEqual(posTracker.getCash(), 0)
        posTracker.buy(1, 10, 0.01)
        self.assertEqual(posTracker.getCash(), -10.01)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        posTracker.sell(1, 10.02, 0.01)
        self.assertEqual(round(posTracker.getCash(), 2), 0)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        # We need to round to avoid floating point errors.
        # The same issue can be reproduced with this piece of code:
        # a = 10.02 - 10
        # b = 0.02
        # print a - b
        # print a - b == 0
        self.assertEqual(posTracker.getShares(), 0)
        self.assertEqual(round(posTracker.getNetProfit(), 2), 0)
        self.assertEqual(round(posTracker.getReturn(), 2), 0)

    def testBuyAndSellWin(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 1)
        self.assertTrue(posTracker.getReturn() == 0.1)

    def testBuyAndSellInTwoTrades(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(2, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        self.assertEqual(posTracker.getNetProfit(), 1)
        self.assertEqual(posTracker.getReturn(), 0.05)
        posTracker.sell(1, 12)
        self.assertEqual(posTracker.getNetProfit(), 3)
        self.assertEqual(posTracker.getReturn(), 3/20.0)

    def testBuyAndSellMultipleEvals(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(2, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getNetProfit(9), -2)
        self.assertEqual(posTracker.getNetProfit(10), 0)
        self.assertEqual(posTracker.getNetProfit(11), 2)
        self.assertEqual(posTracker.getReturn(10), 0)

        self.assertEqual(posTracker.getNetProfit(11), 2)
        self.assertEqual(round(posTracker.getReturn(11), 2), 0.1)

        self.assertEqual(posTracker.getNetProfit(20), 20)
        self.assertEqual(posTracker.getReturn(20), 1)

        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        self.assertEqual(posTracker.getNetProfit(11), 2)
        self.assertEqual(posTracker.getReturn(11), 0.1)

        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 1)
        self.assertEqual(posTracker.getReturn(11), 0.05)

    def testSellAndBuyWin(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(1, 13)
        self.assertEqual(posTracker.getCostPerShare(), 13)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getNetProfit(10), 3)
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 3)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.23076923076923, 9))

    def testSellAndBuyMultipleEvals(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(2, 11)
        self.assertEqual(posTracker.getCostPerShare(), 11)
        self.assertEqual(posTracker.getNetProfit(10), 2)
        self.assertEqual(posTracker.getNetProfit(11), 0)
        self.assertEqual(posTracker.getNetProfit(12), -2)
        self.assertEqual(posTracker.getReturn(11), 0)

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 11)
        self.assertEqual(posTracker.getNetProfit(11), 1)
        self.assertEqual(round(posTracker.getReturn(11), 9), round(0.045454545, 9))

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 2)
        self.assertEqual(posTracker.getNetProfit(100), 2)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.090909091, 9))

    def testBuySellBuy(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        self.assertEqual(posTracker.getNetProfit(9), -1)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getNetProfit(10), 0)
        self.assertEqual(posTracker.getNetProfit(11), 1)
        self.assertEqual(posTracker.getReturn(), 0)
        self.assertEqual(posTracker.getReturn(13), 0.3)

        # Closing the long position and short selling 1 @ $13.
        # The cost basis for the new position is $13.
        posTracker.sell(2, 13)
        self.assertEqual(posTracker.getCostPerShare(), 13)
        self.assertEqual(posTracker.getNetProfit(), 3)
        self.assertEqual(round(posTracker.getReturn(), 8), 0.23076923)

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), 6)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.46153846153846, 9))

    def testSellBuySell(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getReturn(), 0)
        self.assertEqual(posTracker.getNetProfit(13), -3)
        self.assertEqual(posTracker.getReturn(13), -0.3)

        # Closing the short position and going long 1 @ $13.
        # The cost basis for the new position is $13.
        posTracker.buy(2, 13)
        self.assertEqual(posTracker.getCostPerShare(), 13)
        self.assertEqual(posTracker.getNetProfit(), -3)
        self.assertEqual(round(posTracker.getReturn(), 9), round(-0.23076923076923, 9))

        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), -6)
        self.assertEqual(round(posTracker.getReturn(), 9), round(-0.46153846153846, 9))

    def testBuyAndSellBreakEvenWithCommision(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10, 0.5)
        self.assertEqual(posTracker.getCostPerShare(), 10)
        posTracker.sell(1, 11, 0.5)
        self.assertEqual(posTracker.getNetProfit(includeCommissions=False), 1)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getReturn(includeCommissions=False), 0.1)
        self.assertEqual(posTracker.getReturn(), 0)

    def testSeparateAndCombined(self):
        posA = returns.PositionTracker(broker.IntegerTraits())
        posA.buy(11, 10)
        posA.sell(11, 30)
        self.assertEqual(posA.getNetProfit(), 20*11)
        self.assertEqual(posA.getReturn(), 2)

        posB = returns.PositionTracker(broker.IntegerTraits())
        posB.sell(100, 1.1)
        posB.buy(100, 1)
        self.assertEqual(round(posB.getNetProfit(), 2), 100*0.1)
        self.assertEqual(round(posB.getReturn(), 2), 0.09)

        combinedReturn = (1 + posA.getReturn()) * (1 + posB.getReturn()) - 1

        combinedPos = returns.PositionTracker(broker.IntegerTraits())
        combinedPos.buy(11, 10)
        combinedPos.sell(11, 30)
        combinedPos.sell(100, 1.1)
        combinedPos.buy(100, 1)
        self.assertEqual(combinedPos.getReturn(), combinedReturn)

    def testProfitReturnsAndCost(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(10, 1)
        self.assertEqual(posTracker.getNetProfit(), 0)
        self.assertEqual(posTracker.getCostPerShare(), 1)
        self.assertEqual(posTracker.getCommissions(), 0)
        self.assertEqual(posTracker.getCash(), -10)

        posTracker.buy(20, 1, 10)
        self.assertEqual(posTracker.getNetProfit(), -10)
        self.assertEqual(posTracker.getCostPerShare(), 1)
        self.assertEqual(posTracker.getCommissions(), 10)
        self.assertEqual(posTracker.getCash(), -40)

        posTracker.sell(30, 1)
        self.assertEqual(posTracker.getCostPerShare(), 0)
        self.assertEqual(posTracker.getNetProfit(), -10)
        self.assertEqual(posTracker.getCash(), -10)
        self.assertEqual(posTracker.getCommissions(), 10)
        self.assertEqual(posTracker.getReturn(), -10/30.0)

        posTracker.buy(10, 1)
        self.assertEqual(posTracker.getNetProfit(), -10)
        self.assertEqual(posTracker.getCostPerShare(), 1)


class ReturnsTestCase(unittest.TestCase):
    TestInstrument = "any"

    def testOneBarReturn(self):
        initialCash = 1000
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 07), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the orders to get them filled on the first (and only) bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False)  # Open: 15.74
        strat.getBroker().placeOrder(order)
        order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True)  # Close: 15.91
        strat.getBroker().placeOrder(order)

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(strat.getBroker().getCash() == initialCash + (15.91 - 15.74))

        finalValue = 1000 - 15.74 + 15.91
        rets = (finalValue - initialCash) / float(initialCash)
        self.assertEqual(stratAnalyzer.getReturns()[-1], rets)

    def testTwoBarReturns_OpenOpen(self):
        initialCash = 15.61
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False)  # Open: 15.61
        strat.getBroker().placeOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, False)  # Open: 15.74

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(strat.getBroker().getCash() == initialCash + (15.74 - 15.61))
        # First day returns: Open vs Close
        self.assertTrue(stratAnalyzer.getReturns()[0] == (15.90 - 15.61) / 15.61)
        # Second day returns: Open vs Prev. day's close
        self.assertTrue(stratAnalyzer.getReturns()[1] == (15.74 - 15.90) / 15.90)

    def testTwoBarReturns_OpenClose(self):
        initialCash = 15.61
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False)  # Open: 15.61
        strat.getBroker().placeOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True)  # Close: 15.91

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(strat.getBroker().getCash() == initialCash + (15.91 - 15.61))
        # First day returns: Open vs Close
        self.assertTrue(stratAnalyzer.getReturns()[0] == (15.90 - 15.61) / 15.61)
        # Second day returns: Close vs Prev. day's close
        self.assertTrue(stratAnalyzer.getReturns()[1] == (15.91 - 15.90) / 15.90)

    def testTwoBarReturns_CloseOpen(self):
        initialCash = 15.9
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, True)  # Close: 15.90
        strat.getBroker().placeOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, False)  # Open: 15.74

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(strat.getBroker().getCash() == initialCash + (15.74 - 15.90))
        # First day returns: 0
        self.assertTrue(stratAnalyzer.getReturns()[0] == 0)
        # Second day returns: Open vs Prev. day's close
        self.assertTrue(stratAnalyzer.getReturns()[1] == (15.74 - 15.90) / 15.90)

    def testTwoBarReturns_CloseClose(self):
        initialCash = 15.90
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, True)  # Close: 15.90
        strat.getBroker().placeOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True)  # Close: 15.91

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(strat.getBroker().getCash() == initialCash + (15.91 - 15.90))
        # First day returns: 0
        self.assertTrue(stratAnalyzer.getReturns()[0] == 0)
        # Second day returns: Open vs Prev. day's close
        self.assertTrue(stratAnalyzer.getReturns()[1] == (15.91 - 15.90) / 15.90)

    def testCumulativeReturn(self):
        initialCash = 33.06
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = position_test.TestStrategy(barFeed, ReturnsTestCase.TestInstrument, initialCash)

        strat.addPosEntry(datetime.datetime(2001, 1, 12), strat.enterLong, ReturnsTestCase.TestInstrument, 1)  # 33.06
        strat.addPosExit(datetime.datetime(2001, 11, 27))  # 14.32

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(initialCash + (14.32 - 33.06), 2))
        self.assertTrue(round(33.06 * (1 + stratAnalyzer.getCumulativeReturns()[-1]), 2) == 14.32)

    def testGoogle2011(self):
        initialValue = 1000000
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("goog-2011-yahoofinance.csv"))

        strat = strategy_test.TestStrategy(barFeed, initialValue)
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1654, True)  # 2011-01-03 close: 604.35
        strat.getBroker().placeOrder(order)

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        finalValue = strat.getBroker().getValue()

        self.assertEqual(round(stratAnalyzer.getCumulativeReturns()[-1], 4), round((finalValue - initialValue) / float(initialValue), 4))

    def testMultipleInstrumentsInterleaved(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("spy", common.get_data_file_path("spy-2010-yahoofinance.csv"), marketsession.NYSE.getTimezone())
        barFeed.addBarsFromCSV("nikkei", common.get_data_file_path("nikkei-2010-yahoofinance.csv"), marketsession.TSE.getTimezone())

        strat = strategy_test.TestStrategy(barFeed, 1000)
        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)

        strat.order("spy", 1)
        strat.run()
        # The cumulative return should be the same if we load nikkei or not.
        self.assertEqual(round(stratAnalyzer.getCumulativeReturns()[-1], 5), 0.01338)

    def testFirstBar(self):
        initialCash = 1000
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        strat.addOrder(datetime.datetime(2001, 01, 02), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False)  # 2001-01-03 Open: 25.25 Close: 32.00

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertEqual(stratAnalyzer.getReturns()[0], 0)
        self.assertEqual(stratAnalyzer.getReturns()[1], (32.00 - 25.25) / 1000)
