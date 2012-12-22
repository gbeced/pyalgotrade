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
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade import broker

import strategy_test
import common

import unittest

class DrawDownTestCase(unittest.TestCase):
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
		self.assertTrue(stratAnalyzer.getMaxDrawDownDuration()== 0)

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
		self.assertTrue(stratAnalyzer.getMaxDrawDownDuration()== 432)

	def testIGE_Broker(self):
		self.__testIGE_BrokerImpl(1)

	def testIGE_Broker2(self):
		self.__testIGE_BrokerImpl(2)

def getTestCases():
	ret = []

	ret.append(DrawDownTestCase("testNoTrades"))
	ret.append(DrawDownTestCase("testIGE_Broker"))
	ret.append(DrawDownTestCase("testIGE_Broker2"))

	return ret

