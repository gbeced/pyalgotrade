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

class ReturnsCalculatorTestCase(unittest.TestCase):
	def testBuyAndSellBreakEven(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(1, 10)
		retCalc.sell(1, 10)
		self.assertTrue(retCalc.calculateReturn(500) == 0)

	def testBuyAndSellWin(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(1, 10)
		retCalc.sell(1, 11)
		self.assertTrue(retCalc.calculateReturn(500) == 0.1)

	def testBuyAndSellMultipleEvals(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(2, 10)
		self.assertTrue(retCalc.calculateReturn(10) == 0)
		self.assertTrue(retCalc.calculateReturn(11) == 0.1)
		self.assertTrue(retCalc.calculateReturn(20) == 1)
		retCalc.sell(1, 11)
		self.assertTrue(retCalc.calculateReturn(11) == 0.1)
		retCalc.sell(1, 10)
		self.assertTrue(retCalc.calculateReturn(11) == 0.05)

	def testSellAndBuyWin(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.sell(1, 11)
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.calculateReturn(500) == 0.1)

	def testSellAndBuyMultipleEvals(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.sell(2, 11)
		self.assertTrue(retCalc.calculateReturn(11) == 0)
		retCalc.buy(1, 10)
		self.assertTrue(round(retCalc.calculateReturn(11), 4) == 0.0476)
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.calculateReturn(500) == 0.1)

	def testBuySellBuy(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(1, 10)
		retCalc.sell(2, 13)
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.calculateReturn(500) == 0.3)

	def testBuyAndUpdate(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.calculateReturn(20) == 1)
		retCalc.update(15)
		self.assertTrue(retCalc.calculateReturn(15) == 0)
		self.assertTrue(round(retCalc.calculateReturn(20), 2) == 0.33)

	def testBuyUpdateAndSell(self):
		retCalc = returns.ReturnsCalculator()
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.calculateReturn(15) == 0.5)

		retCalc.update(15)
		retCalc.sell(1, 20)
		self.assertTrue(round(retCalc.calculateReturn(500), 2) == 0.33)

		retCalc.update(20)
		self.assertTrue(retCalc.calculateReturn(500) == 0)

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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.74))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][0] == datetime.datetime(2001, 12, 07))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][1] == (15.91 - 15.74) / 15.74)

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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.74 - 15.61))
		# First day returns: Open vs Close
		self.assertTrue(stratAnalyzer.getNetReturns()[0][0] == datetime.datetime(2001, 12, 06))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][1] == (15.90 - 15.61) / 15.61)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[1][0] == datetime.datetime(2001, 12, 07))
		self.assertTrue(stratAnalyzer.getNetReturns()[1][1] == (15.74 - 15.90) / 15.90)

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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.61))
		# First day returns: Open vs Close
		self.assertTrue(stratAnalyzer.getNetReturns()[0][0] == datetime.datetime(2001, 12, 06))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][1] == (15.90 - 15.61) / 15.61)
		# Second day returns: Close vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[1][0] == datetime.datetime(2001, 12, 07))
		self.assertTrue(stratAnalyzer.getNetReturns()[1][1] == (15.91 - 15.90) / 15.90)

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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.74 - 15.90))
		# First day returns: 0
		self.assertTrue(stratAnalyzer.getNetReturns()[0][0] == datetime.datetime(2001, 12, 06))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][1] == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[1][0] == datetime.datetime(2001, 12, 07))
		self.assertTrue(stratAnalyzer.getNetReturns()[1][1] == (15.74 - 15.90) / 15.90)

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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.90))
		# First day returns: 0
		self.assertTrue(stratAnalyzer.getNetReturns()[0][0] == datetime.datetime(2001, 12, 06))
		self.assertTrue(stratAnalyzer.getNetReturns()[0][1] == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[1][0] == datetime.datetime(2001, 12, 07))
		self.assertTrue(stratAnalyzer.getNetReturns()[1][1] == (15.91 - 15.90) / 15.90)

def getTestCases():
	ret = []

	ret.append(ReturnsCalculatorTestCase("testBuyAndSellBreakEven"))
	ret.append(ReturnsCalculatorTestCase("testBuyAndSellWin"))
	ret.append(ReturnsCalculatorTestCase("testBuyAndSellMultipleEvals"))
	ret.append(ReturnsCalculatorTestCase("testSellAndBuyWin"))
	ret.append(ReturnsCalculatorTestCase("testSellAndBuyMultipleEvals"))
	ret.append(ReturnsCalculatorTestCase("testBuySellBuy"))
	ret.append(ReturnsCalculatorTestCase("testBuyAndUpdate"))
	ret.append(ReturnsCalculatorTestCase("testBuyUpdateAndSell"))

	ret.append(ReturnsTestCase("testOneBarReturn"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenClose"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseClose"))

	return ret

