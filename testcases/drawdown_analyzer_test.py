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

from pyalgotrade import barfeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import membf
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade import broker
from pyalgotrade import bar

import strategy_test
import common

import unittest
import datetime

def build_bars_from_closing_prices(closingPrices):
	ret = []

	nextDateTime = datetime.datetime.now()
	for closePrice in closingPrices:
		bar_ = bar.Bar(nextDateTime, closePrice, closePrice, closePrice, closePrice, closePrice, closePrice)
		ret.append(bar_)
		nextDateTime = nextDateTime + datetime.timedelta(days=1)
	return ret

class DDHelperCase(unittest.TestCase):
	def testNoDrawDown1(self):
		helper = drawdown.DrawDownHelper(10)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)

	def testNoDrawDown2(self):
		helper = drawdown.DrawDownHelper(10)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)
		helper.update(10.01, 10.01)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)
		helper.update(11, 11)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)

	def testDrawDown1(self):
		helper = drawdown.DrawDownHelper(10)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)
		helper.update(5, 5)
		self.assertEqual(helper.getMaxDrawDown(), -0.5)
		self.assertEqual(helper.getCurrentDrawDown(), -0.5)
		self.assertEqual(helper.getDuration(), 1)
		helper.update(4, 4)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.6)
		self.assertEqual(helper.getDuration(), 2)
		helper.update(4, 4)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.6)
		self.assertEqual(helper.getDuration(), 3)
		helper.update(5, 5)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.5)
		self.assertEqual(helper.getDuration(), 4)
		helper.update(9, 9)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.1)
		self.assertEqual(helper.getDuration(), 5)
		helper.update(9.9, 9.9)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(round(helper.getCurrentDrawDown(), 2), -0.01)
		self.assertEqual(helper.getDuration(), 6)

	def testDrawDown2(self):
		helper = drawdown.DrawDownHelper(10)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)
		helper.update(5, 5)
		self.assertEqual(helper.getMaxDrawDown(), -0.5)
		self.assertEqual(helper.getCurrentDrawDown(), -0.5)
		self.assertEqual(helper.getDuration(), 1)
		helper.update(4, 4)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.6)
		self.assertEqual(helper.getDuration(), 2)
		helper.update(4, 4)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.6)
		self.assertEqual(helper.getDuration(), 3)
		helper.update(5, 5)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.5)
		self.assertEqual(helper.getDuration(), 4)
		helper.update(9, 9)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(helper.getCurrentDrawDown(), -0.1)
		self.assertEqual(helper.getDuration(), 5)
		helper.update(9.9, 9.9)
		self.assertEqual(helper.getMaxDrawDown(), -0.6)
		self.assertEqual(round(helper.getCurrentDrawDown(), 2), -0.01)
		self.assertEqual(helper.getDuration(), 6)

		helper.update(20, 20)
		self.assertEqual(helper.getMaxDrawDown(), 0)
		self.assertEqual(helper.getCurrentDrawDown(), 0)
		self.assertEqual(helper.getDuration(), 0)
		helper.update(10, 10)
		self.assertEqual(helper.getMaxDrawDown(), -0.5)
		self.assertEqual(helper.getCurrentDrawDown(), -0.5)
		self.assertEqual(helper.getDuration(), 1)

class AnalyzerTestCase(unittest.TestCase):
	def testNoTrades(self):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("sharpe-ratio-test-spy.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.setBrokerOrdersGTC(True)
		strat.getBroker().setUseAdjustedValues(True)
		stratAnalyzer = drawdown.DrawDown()
		strat.attachAnalyzer(stratAnalyzer)

		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000)
		self.assertTrue(strat.getOrderUpdatedEvents() == 0)
		self.assertTrue(stratAnalyzer.getMaxDrawDown() == 0)
		self.assertTrue(stratAnalyzer.getLongestDrawDownDuration()== 0)

	def __testIGE_BrokerImpl(self, quantity):
		initialCash = 42.09*quantity
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, initialCash)
		strat.getBroker().setUseAdjustedValues(True)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = drawdown.DrawDown()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place the order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", quantity, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(strategy_test.datetime_from_date(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", quantity, True) # Adj. Close: 127.64
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == initialCash + (127.64 - 42.09) * quantity)
		self.assertTrue(strat.getOrderUpdatedEvents() == 2)
		self.assertTrue(round(stratAnalyzer.getMaxDrawDown(), 5) == 0.31178)
		self.assertTrue(stratAnalyzer.getLongestDrawDownDuration()== 432)

	def testIGE_Broker(self):
		self.__testIGE_BrokerImpl(1)

	def testIGE_Broker2(self):
		self.__testIGE_BrokerImpl(2)

	def __testManualImpl(self, closingPrices, cash):
		barFeed = membf.Feed(barfeed.Frequency.DAY)
		bars = build_bars_from_closing_prices(closingPrices)
		barFeed.addBarsFromSequence("orcl", bars)

		strat = strategy_test.TestStrategy(barFeed, cash)
		stratAnalyzer = drawdown.DrawDown()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place the order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "orcl", 1, True)
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)

		strat.run()
		return stratAnalyzer

	def testManual_NoDD(self):
		# No drawdown
		stratAnalyzer = self.__testManualImpl([10, 10, 10], 10)
		self.assertEqual(round(stratAnalyzer.getMaxDrawDown(), 2), 0)
		self.assertEqual(stratAnalyzer.getLongestDrawDownDuration(), 0)

	def testManual_1DD(self):
		stratAnalyzer = self.__testManualImpl([10, 9, 8], 10)
		self.assertEqual(round(stratAnalyzer.getMaxDrawDown(), 2), 0.2)
		self.assertEqual(stratAnalyzer.getLongestDrawDownDuration(), 2)

	def testManual_2DD(self):
		stratAnalyzer = self.__testManualImpl([10, 9.5, 9, 8, 11, 8], 10)
		self.assertEqual(round(stratAnalyzer.getMaxDrawDown(), 2), 0.27)
		self.assertEqual(stratAnalyzer.getLongestDrawDownDuration(), 3)

def getTestCases():
	ret = []

	ret.append(DDHelperCase("testNoDrawDown1"))
	ret.append(DDHelperCase("testNoDrawDown2"))
	ret.append(DDHelperCase("testDrawDown1"))
	ret.append(DDHelperCase("testDrawDown2"))

	ret.append(AnalyzerTestCase("testNoTrades"))
	ret.append(AnalyzerTestCase("testIGE_Broker"))
	ret.append(AnalyzerTestCase("testIGE_Broker2"))
	ret.append(AnalyzerTestCase("testManual_NoDD"))
	ret.append(AnalyzerTestCase("testManual_1DD"))
	ret.append(AnalyzerTestCase("testManual_2DD"))

	return ret

