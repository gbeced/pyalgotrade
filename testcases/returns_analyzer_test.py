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
	invalid_price = 5000

	def testBuyAndSellBreakEven(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10)
		retCalc.sell(1, 10)
		self.assertTrue(retCalc.getCost() == 10)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 0)
		self.assertTrue(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price) == 0)

	def testBuyAndSellWin(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10)
		retCalc.sell(1, 11)
		self.assertTrue(retCalc.getCost() == 10)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 1)
		self.assertTrue(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price) == 0.1)

	def testBuyAndSellMultipleEvals(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(2, 10)
		self.assertTrue(retCalc.getCost() == 20)
		self.assertTrue(retCalc.getNetProfit(10) == 0)
		self.assertTrue(retCalc.getReturn(10) == 0)

		self.assertTrue(retCalc.getNetProfit(11) == 2)
		self.assertTrue(retCalc.getReturn(11) == 0.1)

		self.assertTrue(retCalc.getNetProfit(20) == 20)
		self.assertTrue(retCalc.getReturn(20) == 1)

		retCalc.sell(1, 11)
		self.assertTrue(retCalc.getCost() == 20)
		self.assertTrue(retCalc.getNetProfit(11) == 2)
		self.assertTrue(retCalc.getReturn(11) == 0.1)

		retCalc.sell(1, 10)
		self.assertTrue(retCalc.getCost() == 20)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 1)
		self.assertTrue(retCalc.getReturn(11) == 0.05)

	def testSellAndBuyWin(self):
		retCalc = returns.ReturnCalculator()
		retCalc.sell(1, 11)
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 11)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 1)
		self.assertTrue(round(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price), 4) == round(0.090909091, 4))

	def testSellAndBuyMultipleEvals(self):
		retCalc = returns.ReturnCalculator()
		retCalc.sell(2, 11)
		self.assertTrue(retCalc.getCost() == 22)
		self.assertTrue(retCalc.getNetProfit(11) == 0)
		self.assertTrue(retCalc.getReturn(11) == 0)

		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 22)
		self.assertTrue(retCalc.getNetProfit(11) == 1)
		self.assertTrue(round(retCalc.getReturn(11), 4) == round(0.045454545, 4))

		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 22)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 2)
		self.assertTrue(round(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price), 4) == round(0.090909091, 4))

	def testBuySellBuy(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 10)

		retCalc.sell(2, 13) # Short selling 1 @ $13
		self.assertTrue(retCalc.getCost() == 10 + 13)

		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 10 + 13)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 6)
		self.assertTrue(round(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price), 4) == round(0.260869565, 4))

	def testBuyAndUpdate(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 10)
		self.assertTrue(retCalc.getNetProfit(20) == 10)
		self.assertTrue(retCalc.getReturn(20) == 1)

		retCalc.updatePrice(15)
		self.assertTrue(retCalc.getCost() == 15)
		self.assertTrue(retCalc.getNetProfit(15) == 0)
		self.assertTrue(retCalc.getReturn(15) == 0)

		self.assertTrue(retCalc.getNetProfit(20) == 5)
		self.assertTrue(round(retCalc.getReturn(20), 2) == 0.33)

	def testBuyUpdateAndSell(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10)
		self.assertTrue(retCalc.getCost() == 10)
		self.assertTrue(retCalc.getNetProfit(15) == 5)
		self.assertTrue(retCalc.getReturn(15) == 0.5)

		retCalc.updatePrice(15)
		self.assertTrue(retCalc.getCost() == 15)
		retCalc.sell(1, 20)
		self.assertTrue(retCalc.getCost() == 15)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 5)
		self.assertTrue(round(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price), 2) == 0.33)

		retCalc.updatePrice(100)
		self.assertTrue(retCalc.getCost() == 0)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 0)
		self.assertTrue(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price) == 0)

	def testBuyAndSellBreakEvenWithCommision(self):
		retCalc = returns.ReturnCalculator()
		retCalc.buy(1, 10, 0.5)
		retCalc.sell(1, 11, 0.5)
		self.assertTrue(retCalc.getCost() == 10)
		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price, False) == 1)
		self.assertTrue(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price, False) == 0.1)

		self.assertTrue(retCalc.getNetProfit(ReturnsCalculatorTestCase.invalid_price, True) == 0)
		self.assertTrue(retCalc.getReturn(ReturnsCalculatorTestCase.invalid_price, True) == 0)

	def testLongShortEqualAmount(self):
		retCalcXYZ = returns.ReturnCalculator()
		retCalcXYZ.buy(11, 10)
		retCalcXYZ.sell(11, 30)
		self.assertTrue(retCalcXYZ.getCost() == 11*10)
		self.assertTrue(retCalcXYZ.getNetProfit(ReturnsCalculatorTestCase.invalid_price) == 20*11)
		self.assertTrue(retCalcXYZ.getReturn(ReturnsCalculatorTestCase.invalid_price) == 2)

		retCalcABC = returns.ReturnCalculator()
		retCalcABC.sell(100, 1.1)
		retCalcABC.buy(100, 1)
		self.assertTrue(retCalcABC.getCost() == 100*1.1)
		self.assertTrue(round(retCalcABC.getNetProfit(ReturnsCalculatorTestCase.invalid_price), 2) == 100*0.1)
		self.assertEqual(round(retCalcABC.getReturn(ReturnsCalculatorTestCase.invalid_price), 2), 0.09)

		combinedCost = retCalcXYZ.getCost() + retCalcABC.getCost()
		combinedPL = retCalcXYZ.getNetProfit(ReturnsCalculatorTestCase.invalid_price) + retCalcABC.getNetProfit(ReturnsCalculatorTestCase.invalid_price)
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

		stratAnalyzer = returns.ReturnsAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)
		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000 + (15.91 - 15.74))
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 07)] == (15.91 - 15.74) / 15.74)

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
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 06)] == (15.90 - 15.61) / 15.61)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 07)] == (15.74 - 15.90) / 15.90)

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
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 06)] == (15.90 - 15.61) / 15.61)
		# Second day returns: Close vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 07)] == (15.91 - 15.90) / 15.90)

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
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 06)] == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 07)] == (15.74 - 15.90) / 15.90)

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
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 06)] == 0)
		# Second day returns: Open vs Prev. day's close
		self.assertTrue(stratAnalyzer.getNetReturns()[datetime.datetime(2001, 12, 07)] == (15.91 - 15.90) / 15.90)

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
	ret.append(ReturnsCalculatorTestCase("testBuyAndSellBreakEvenWithCommision"))
	ret.append(ReturnsCalculatorTestCase("testLongShortEqualAmount"))

	ret.append(ReturnsTestCase("testOneBarReturn"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenClose"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseClose"))

	return ret

