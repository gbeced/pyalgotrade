# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

import strategy_test
import common

import unittest
import datetime

class PosTrackerTestCase(unittest.TestCase):
	invalid_price = 5000

	def testBuyAndSellBreakEven(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10)
		posTracker.sell(1, 10)
		self.assertTrue(posTracker.getCost() == 10)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 0)
		self.assertTrue(posTracker.getReturn(PosTrackerTestCase.invalid_price) == 0)

	def testBuyAndSellWin(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10)
		posTracker.sell(1, 11)
		self.assertTrue(posTracker.getCost() == 10)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 1)
		self.assertTrue(posTracker.getReturn(PosTrackerTestCase.invalid_price) == 0.1)

	def testBuyAndSellMultipleEvals(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(2, 10)
		self.assertTrue(posTracker.getCost() == 20)
		self.assertTrue(posTracker.getNetProfit(10) == 0)
		self.assertTrue(posTracker.getReturn(10) == 0)

		self.assertTrue(posTracker.getNetProfit(11) == 2)
		self.assertTrue(posTracker.getReturn(11) == 0.1)

		self.assertTrue(posTracker.getNetProfit(20) == 20)
		self.assertTrue(posTracker.getReturn(20) == 1)

		posTracker.sell(1, 11)
		self.assertTrue(posTracker.getCost() == 20)
		self.assertTrue(posTracker.getNetProfit(11) == 2)
		self.assertTrue(posTracker.getReturn(11) == 0.1)

		posTracker.sell(1, 10)
		self.assertTrue(posTracker.getCost() == 20)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 1)
		self.assertTrue(posTracker.getReturn(11) == 0.05)

	def testSellAndBuyWin(self):
		posTracker = returns.PositionTracker()
		posTracker.sell(1, 11)
		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 11)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 1)
		self.assertTrue(round(posTracker.getReturn(PosTrackerTestCase.invalid_price), 4) == round(0.090909091, 4))

	def testSellAndBuyMultipleEvals(self):
		posTracker = returns.PositionTracker()
		posTracker.sell(2, 11)
		self.assertTrue(posTracker.getCost() == 22)
		self.assertTrue(posTracker.getNetProfit(11) == 0)
		self.assertTrue(posTracker.getReturn(11) == 0)

		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 22)
		self.assertTrue(posTracker.getNetProfit(11) == 1)
		self.assertTrue(round(posTracker.getReturn(11), 4) == round(0.045454545, 4))

		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 22)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 2)
		self.assertTrue(round(posTracker.getReturn(PosTrackerTestCase.invalid_price), 4) == round(0.090909091, 4))

	def testBuySellBuy(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 10)

		posTracker.sell(2, 13) # Short selling 1 @ $13
		self.assertTrue(posTracker.getCost() == 10 + 13)

		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 10 + 13)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 6)
		self.assertTrue(round(posTracker.getReturn(PosTrackerTestCase.invalid_price), 4) == round(0.260869565, 4))

	def testBuyAndUpdate(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 10)
		self.assertTrue(posTracker.getNetProfit(20) == 10)
		self.assertTrue(posTracker.getReturn(20) == 1)

		posTracker.update(15)
		self.assertTrue(posTracker.getCost() == 15)
		self.assertTrue(posTracker.getNetProfit(15) == 0)
		self.assertTrue(posTracker.getReturn(15) == 0)

		self.assertTrue(posTracker.getNetProfit(20) == 5)
		self.assertTrue(round(posTracker.getReturn(20), 2) == 0.33)

	def testBuyUpdateAndSell(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10)
		self.assertTrue(posTracker.getCost() == 10)
		self.assertTrue(posTracker.getNetProfit(15) == 5)
		self.assertTrue(posTracker.getReturn(15) == 0.5)

		posTracker.update(15)
		self.assertTrue(posTracker.getCost() == 15)
		posTracker.sell(1, 20)
		self.assertTrue(posTracker.getCost() == 15)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 5)
		self.assertTrue(round(posTracker.getReturn(PosTrackerTestCase.invalid_price), 2) == 0.33)

		posTracker.update(100)
		self.assertTrue(posTracker.getCost() == 0)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price) == 0)
		self.assertTrue(posTracker.getReturn(PosTrackerTestCase.invalid_price) == 0)

	def testBuyAndSellBreakEvenWithCommision(self):
		posTracker = returns.PositionTracker()
		posTracker.buy(1, 10, 0.5)
		posTracker.sell(1, 11, 0.5)
		self.assertTrue(posTracker.getCost() == 10)
		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price, False) == 1)
		self.assertTrue(posTracker.getReturn(PosTrackerTestCase.invalid_price, False) == 0.1)

		self.assertTrue(posTracker.getNetProfit(PosTrackerTestCase.invalid_price, True) == 0)
		self.assertTrue(posTracker.getReturn(PosTrackerTestCase.invalid_price, True) == 0)

	def testLongShortEqualAmount(self):
		posTrackerXYZ = returns.PositionTracker()
		posTrackerXYZ.buy(11, 10)
		posTrackerXYZ.sell(11, 30)
		self.assertTrue(posTrackerXYZ.getCost() == 11*10)
		self.assertTrue(posTrackerXYZ.getNetProfit(PosTrackerTestCase.invalid_price) == 20*11)
		self.assertTrue(posTrackerXYZ.getReturn(PosTrackerTestCase.invalid_price) == 2)

		posTrackerABC = returns.PositionTracker()
		posTrackerABC.sell(100, 1.1)
		posTrackerABC.buy(100, 1)
		self.assertTrue(posTrackerABC.getCost() == 100*1.1)
		self.assertTrue(round(posTrackerABC.getNetProfit(PosTrackerTestCase.invalid_price), 2) == 100*0.1)
		self.assertEqual(round(posTrackerABC.getReturn(PosTrackerTestCase.invalid_price), 2), 0.09)

		combinedCost = posTrackerXYZ.getCost() + posTrackerABC.getCost()
		combinedPL = posTrackerXYZ.getNetProfit(PosTrackerTestCase.invalid_price) + posTrackerABC.getNetProfit(PosTrackerTestCase.invalid_price)
		combinedReturn = combinedPL / float(combinedCost)
		self.assertTrue(round(combinedReturn, 9) == 1.045454545)

class ReturnsTestCase(unittest.TestCase):
	TestInstrument = "any"
	
	def testOneBarReturn(self):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 07), datetime.datetime(2001, 12, 07)))
		barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)

		# 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
		# Manually place the orders to get them filled on the first (and only) bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False) # Open: 15.74
		strat.getBroker().placeOrder(order)
		order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True) # Close: 15.91
		strat.getBroker().placeOrder(order)

		stratAnalyzer = returns.Returns()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.74))
		self.assertTrue(stratAnalyzer.getNetReturn() == (15.91 - 15.74) / 15.74)

	def testTwoBarReturns_OpenOpen(self):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
		barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)

		# 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
		# 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
		# Manually place the entry order, to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False) # Open: 15.61
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, False) # Open: 15.74

		stratAnalyzer = returns.Returns()
		strat.attachAnalyzer(stratAnalyzer)
		returnsDS = returns.ReturnsDataSeries(strat)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.74 - 15.61))
		# First day returns: Open vs Close
		self.assertTrue(returnsDS.getValueAbsolute(0) == (15.90 - 15.61) / 15.61)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(returnsDS.getValueAbsolute(1) == (15.74 - 15.90) / 15.90)

	def testTwoBarReturns_OpenClose(self):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
		barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)

		# 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
		# 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
		# Manually place the entry order, to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, False) # Open: 15.61
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True) # Close: 15.91

		stratAnalyzer = returns.Returns()
		strat.attachAnalyzer(stratAnalyzer)
		returnsDS = returns.ReturnsDataSeries(strat)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.61))
		# First day returns: Open vs Close
		self.assertTrue(returnsDS.getValueAbsolute(0) == (15.90 - 15.61) / 15.61)
		# Second day returns: Close vs Prev. day's close
		self.assertTrue(returnsDS.getValueAbsolute(1) == (15.91 - 15.90) / 15.90)

	def testTwoBarReturns_CloseOpen(self):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
		barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)

		# 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
		# 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
		# Manually place the entry order, to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, True) # Close: 15.90
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, False) # Open: 15.74

		stratAnalyzer = returns.Returns()
		strat.attachAnalyzer(stratAnalyzer)
		returnsDS = returns.ReturnsDataSeries(strat)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.74 - 15.90))
		# First day returns: 0
		self.assertTrue(returnsDS.getValueAbsolute(0) == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(returnsDS.getValueAbsolute(1) == (15.74 - 15.90) / 15.90)

	def testTwoBarReturns_CloseClose(self):
		barFeed = yahoofeed.Feed()
		barFeed.setBarFilter(csvfeed.DateRangeFilter(datetime.datetime(2001, 12, 06), datetime.datetime(2001, 12, 07)))
		barFeed.addBarsFromCSV(ReturnsTestCase.TestInstrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)

		# 2001-12-06,15.61,16.03,15.50,15.90,66944900,15.55
		# 2001-12-07,15.74,15.95,15.55,15.91,42463200,15.56
		# Manually place the entry order, to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, ReturnsTestCase.TestInstrument, 1, True) # Close: 15.90
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2001, 12, 06), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True) # Close: 15.91

		stratAnalyzer = returns.Returns()
		strat.attachAnalyzer(stratAnalyzer)
		returnsDS = returns.ReturnsDataSeries(strat)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.90))
		# First day returns: 0
		self.assertTrue(returnsDS.getValueAbsolute(0) == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(returnsDS.getValueAbsolute(1) == (15.91 - 15.90) / 15.90)

def getTestCases():
	ret = []

	ret.append(PosTrackerTestCase("testBuyAndSellBreakEven"))
	ret.append(PosTrackerTestCase("testBuyAndSellWin"))
	ret.append(PosTrackerTestCase("testBuyAndSellMultipleEvals"))
	ret.append(PosTrackerTestCase("testSellAndBuyWin"))
	ret.append(PosTrackerTestCase("testSellAndBuyMultipleEvals"))
	ret.append(PosTrackerTestCase("testBuySellBuy"))
	ret.append(PosTrackerTestCase("testBuyAndUpdate"))
	ret.append(PosTrackerTestCase("testBuyUpdateAndSell"))
	ret.append(PosTrackerTestCase("testBuyAndSellBreakEvenWithCommision"))
	ret.append(PosTrackerTestCase("testLongShortEqualAmount"))

	ret.append(ReturnsTestCase("testOneBarReturn"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenClose"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseClose"))

	return ret

