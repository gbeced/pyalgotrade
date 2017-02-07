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

import datetime

import common
import strategy_test
import position_test

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.stratanalyzer import returns
from pyalgotrade import broker
from pyalgotrade import marketsession


class TimeWeightedReturnsTestCase(common.TestCase):
    def testNullPortfolio(self):
        retTracker = returns.TimeWeightedReturns(0)
        self.assertEqual(retTracker.getCumulativeReturns(), 0)

    def testNoUpdates(self):
        retTracker = returns.TimeWeightedReturns(10)
        self.assertEqual(retTracker.getCumulativeReturns(), 0)

    def testInvestopedia(self):
        # http://www.investopedia.com/exam-guide/cfa-level-1/quantitative-methods/discounted-cash-flow-time-weighted-return.asp
        retTracker = returns.TimeWeightedReturns(200000)
        retTracker.update(196500)  # March 31, 2004
        self.assertEquals(round(retTracker.getLastPeriodReturns(), 4), -0.0175)
        retTracker.update(200000)  # June 30, 2004
        self.assertEquals(round(retTracker.getLastPeriodReturns(), 4), 0.0178)
        retTracker.deposit(20000)
        retTracker.update(222000)  # July 30, 2004
        self.assertEquals(round(retTracker.getLastPeriodReturns(), 2), 0.01)
        retTracker.update(243000)  # Sept. 30, 2004
        self.assertEquals(round(retTracker.getLastPeriodReturns(), 4), 0.0946)
        retTracker.deposit(2000)
        retTracker.update(250000)  # Dec. 31, 2004
        self.assertEquals(round(retTracker.getLastPeriodReturns(), 4), 0.0206)
        self.assertEquals(round(retTracker.getCumulativeReturns(), 6),  0.128288)


class PosTrackerTestCase(common.TestCase):
    def testBuyAndSellBreakEven(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        posTracker.sell(1, 10)
        # self.assertEqual(posTracker.getCash(), 0)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getReturn(), 0)

    def testBuyAndSellBreakEvenWithCommission(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        # self.assertEqual(posTracker.getCash(), 0)
        posTracker.buy(1, 10, 0.01)
        # self.assertEqual(posTracker.getCash(), -10.01)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        posTracker.sell(1, 10.02, 0.01)
        # self.assertEqual(round(posTracker.getCash(), 2), 0)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        # We need to round to avoid floating point errors.
        # The same issue can be reproduced with this piece of code:
        # a = 10.02 - 10
        # b = 0.02
        # print a - b
        # print a - b == 0
        self.assertEqual(posTracker.getPosition(), 0)
        self.assertEqual(round(posTracker.getPnL(), 2), 0)
        self.assertEqual(round(posTracker.getReturn(), 2), 0)

    def testBuyAndSellWin(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 1)
        self.assertTrue(posTracker.getReturn() == 0.1)

    def testBuyAndSellInTwoTrades(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(2, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        self.assertEqual(posTracker.getPnL(), 1)
        self.assertEqual(posTracker.getReturn(), 0.05)
        posTracker.sell(1, 12)
        self.assertEqual(posTracker.getPnL(), 3)
        self.assertEqual(posTracker.getReturn(), 3/20.0)

    def testBuyAndSellMultipleEvals(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(2, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getPnL(price=9), -2)
        self.assertEqual(posTracker.getPnL(price=10), 0)
        self.assertEqual(posTracker.getPnL(price=11), 2)
        self.assertEqual(posTracker.getReturn(10), 0)

        self.assertEqual(posTracker.getPnL(price=11), 2)
        self.assertEqual(round(posTracker.getReturn(11), 2), 0.1)

        self.assertEqual(posTracker.getPnL(price=20), 20)
        self.assertEqual(posTracker.getReturn(20), 1)

        posTracker.sell(1, 11)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        self.assertEqual(posTracker.getPnL(price=11), 2)
        self.assertEqual(posTracker.getReturn(11), 0.1)

        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 1)
        self.assertEqual(posTracker.getReturn(11), 0.05)

    def testSellAndBuyWin(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(1, 13)
        self.assertEqual(posTracker.getAvgPrice(), 13)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getPnL(price=10), 3)
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 3)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.23076923076923, 9))

    def testSellAndBuyMultipleEvals(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(2, 11)
        self.assertEqual(posTracker.getAvgPrice(), 11)
        self.assertEqual(posTracker.getPnL(price=10), 2)
        self.assertEqual(posTracker.getPnL(price=11), 0)
        self.assertEqual(posTracker.getPnL(price=12), -2)
        self.assertEqual(posTracker.getReturn(11), 0)

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 11)
        self.assertEqual(posTracker.getPnL(price=11), 1)
        self.assertEqual(round(posTracker.getReturn(11), 9), round(0.045454545, 9))

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 2)
        self.assertEqual(posTracker.getPnL(price=100), 2)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.090909091, 9))

    def testBuySellBuy(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        self.assertEqual(posTracker.getPnL(price=9), -1)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getPnL(price=10), 0)
        self.assertEqual(posTracker.getPnL(price=11), 1)
        self.assertEqual(posTracker.getReturn(), 0)
        self.assertEqual(posTracker.getReturn(13), 0.3)

        # Closing the long position and short selling 1 @ $13.
        # The cost basis for the new position is $13.
        posTracker.sell(2, 13)
        self.assertEqual(posTracker.getAvgPrice(), 13)
        self.assertEqual(posTracker.getPnL(), 3)
        self.assertEqual(round(posTracker.getReturn(), 8), 0.23076923)

        posTracker.buy(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), 6)
        self.assertEqual(round(posTracker.getReturn(), 9), round(0.46153846153846, 9))

    def testSellBuySell(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getReturn(), 0)
        self.assertEqual(posTracker.getPnL(price=13), -3)
        self.assertEqual(posTracker.getReturn(13), -0.3)

        # Closing the short position and going long 1 @ $13.
        # The cost basis for the new position is $13.
        posTracker.buy(2, 13)
        self.assertEqual(posTracker.getAvgPrice(), 13)
        self.assertEqual(posTracker.getPnL(), -3)
        self.assertEqual(round(posTracker.getReturn(), 9), round(-0.23076923076923, 9))

        posTracker.sell(1, 10)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), -6)
        self.assertEqual(round(posTracker.getReturn(), 9), round(-0.46153846153846, 9))

    def testBuyAndSellBreakEvenWithCommision(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(1, 10, 0.5)
        self.assertEqual(posTracker.getAvgPrice(), 10)
        posTracker.sell(1, 11, 0.5)
        self.assertEqual(posTracker.getPnL(includeCommissions=False), 1)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getReturn(includeCommissions=False), 0.1)
        self.assertEqual(posTracker.getReturn(), 0)

    def testSeparateAndCombined(self):
        posA = returns.PositionTracker(broker.IntegerTraits())
        posA.buy(11, 10)
        posA.sell(11, 30)
        self.assertEqual(posA.getPnL(), 20*11)
        self.assertEqual(posA.getReturn(), 2)

        posB = returns.PositionTracker(broker.IntegerTraits())
        posB.sell(100, 1.1)
        posB.buy(100, 1)
        self.assertEqual(round(posB.getPnL(), 2), 100*0.1)
        self.assertEqual(round(posB.getReturn(), 2), 0.09)

        combinedPos = returns.PositionTracker(broker.IntegerTraits())
        combinedPos.buy(11, 10)
        combinedPos.sell(11, 30)
        combinedPos.sell(100, 1.1)
        combinedPos.buy(100, 1)
        self.assertEqual(round(combinedPos.getReturn(), 6), 2.090909)
        # The return of the combined position is less than the two returns combined
        # because when the second position gets opened the amount of cash not invested is greater
        # than that of posB alone.
        self.assertLess(round(combinedPos.getReturn(), 6), ((1+posA.getReturn())*(1+posB.getReturn())-1))

    def testProfitReturnsAndCost(self):
        posTracker = returns.PositionTracker(broker.IntegerTraits())
        posTracker.buy(10, 1)
        self.assertEqual(posTracker.getPnL(), 0)
        self.assertEqual(posTracker.getAvgPrice(), 1)
        self.assertEqual(posTracker.getCommissions(), 0)
        # self.assertEqual(posTracker.getCash(), -10)

        posTracker.buy(20, 1, 10)
        self.assertEqual(posTracker.getPnL(), -10)
        self.assertEqual(posTracker.getAvgPrice(), 1)
        self.assertEqual(posTracker.getCommissions(), 10)
        # self.assertEqual(posTracker.getCash(), -40)

        posTracker.sell(30, 1)
        self.assertEqual(posTracker.getAvgPrice(), 0)
        self.assertEqual(posTracker.getPnL(), -10)
        # self.assertEqual(posTracker.getCash(), -10)
        self.assertEqual(posTracker.getCommissions(), 10)
        self.assertEqual(posTracker.getReturn(), -10/30.0)

        posTracker.buy(10, 1)
        self.assertEqual(posTracker.getPnL(), -10)
        self.assertEqual(posTracker.getAvgPrice(), 1)


class AnalyzerTestCase(common.TestCase):
    TestInstrument = "any"

    def testOneBarReturn(self):
        initialCash = 1000
        barFeed = yahoofeed.Feed()
        barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 07), datetime.datetime(2001, 12, 07)))
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the orders to get them filled on the first (and only) bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, False)  # Open: 15.74
        strat.getBroker().submitOrder(order)
        order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL, AnalyzerTestCase.TestInstrument, 1, True)  # Close: 15.91
        strat.getBroker().submitOrder(order)

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
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, False)  # Open: 15.61
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, AnalyzerTestCase.TestInstrument, 1, False)  # Open: 15.74

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
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, False)  # Open: 15.61
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, AnalyzerTestCase.TestInstrument, 1, True)  # Close: 15.91

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
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, True)  # Close: 15.90
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, AnalyzerTestCase.TestInstrument, 1, False)  # Open: 15.74

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
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        # 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
        # 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
        # Manually place the entry order, to get it filled on the first bar.
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, True)  # Close: 15.90
        strat.getBroker().submitOrder(order)
        strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, AnalyzerTestCase.TestInstrument, 1, True)  # Close: 15.91

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
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = position_test.TestStrategy(barFeed, AnalyzerTestCase.TestInstrument, initialCash)

        strat.addPosEntry(datetime.datetime(2001, 1, 12), strat.enterLong, AnalyzerTestCase.TestInstrument, 1)  # 33.06
        strat.addPosExitMarket(datetime.datetime(2001, 11, 27))  # 14.32

        stratAnalyzer = returns.Returns(maxLen=10)
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(initialCash + (14.32 - 33.06), 2))
        self.assertTrue(round(33.06 * (1 + stratAnalyzer.getCumulativeReturns()[-1]), 2) == 14.32)
        self.assertEqual(len(stratAnalyzer.getCumulativeReturns()), 10)
        self.assertEqual(len(stratAnalyzer.getReturns()), 10)

    def testGoogle2011(self):
        initialValue = 1000000
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("goog-2011-yahoofinance.csv"))

        strat = strategy_test.TestStrategy(barFeed, initialValue)
        order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1654, True)  # 2011-01-03 close: 604.35
        strat.getBroker().submitOrder(order)

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        finalValue = strat.getBroker().getEquity()

        self.assertEqual(round(stratAnalyzer.getCumulativeReturns()[-1], 4), round((finalValue - initialValue) / float(initialValue), 4))

    def testMultipleInstrumentsInterleaved(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV("spy", common.get_data_file_path("spy-2010-yahoofinance.csv"), marketsession.NYSE.getTimezone())
        barFeed.addBarsFromCSV("nikkei", common.get_data_file_path("nikkei-2010-yahoofinance.csv"), marketsession.TSE.getTimezone())

        strat = strategy_test.TestStrategy(barFeed, 1000)
        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)

        strat.marketOrder("spy", 1)
        strat.run()
        # The cumulative return should be the same if we load nikkei or not.
        self.assertEqual(round(stratAnalyzer.getCumulativeReturns()[-1], 5), 0.01338)

    def testFirstBar(self):
        initialCash = 1000
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(AnalyzerTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        strat = strategy_test.TestStrategy(barFeed, initialCash)

        strat.addOrder(datetime.datetime(2001, 01, 02), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, AnalyzerTestCase.TestInstrument, 1, False)  # 2001-01-03 Open: 25.25 Close: 32.00

        stratAnalyzer = returns.Returns()
        strat.attachAnalyzer(stratAnalyzer)
        strat.run()
        self.assertEqual(stratAnalyzer.getReturns()[0], 0)
        self.assertEqual(stratAnalyzer.getReturns()[1], (32.00 - 25.25) / 1000)

        # Check date times.
        datetimes = barFeed[AnalyzerTestCase.TestInstrument].getDateTimes()
        for i in [0, -1]:
            self.assertEqual(stratAnalyzer.getReturns().getDateTimes()[i], datetimes[i])
            self.assertEqual(stratAnalyzer.getCumulativeReturns().getDateTimes()[i], datetimes[i])
