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
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.broker import backtesting
from pyalgotrade import broker

import strategy_test
import common

import unittest
import datetime

class SharpeRatioTestCase(unittest.TestCase):
	def testNoTrades(self):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000)
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252) / 10**14, 4) == -7.1486)
		self.assertTrue(stratAnalyzer.getSharpeRatio(0, 252) == None)

	def __testIGE_BrokerImpl(self, quantity):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.getBroker().setUseAdjustedValues(True)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place the order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", quantity, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", quantity, True) # Adj. Close: 127.64
		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000 + (127.64 - 42.09) * quantity)
		self.assertTrue(strat.getOrderUpdatedEvents() == 2)
		# The results are slightly different different only because I'm taking into account the first bar as well.
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252), 4) == 0.7889)

	def testIGE_Broker(self):
		self.__testIGE_BrokerImpl(1)

	def testIGE_Broker2(self):
		self.__testIGE_BrokerImpl(2)

	def testIGE_BrokerWithCommission(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		brk = backtesting.Broker(1000, barFeed, broker.FixedCommission(0.5))
		strat = strategy_test.TestStrategy(barFeed, 1000, brk)
		strat.getBroker().setUseAdjustedValues(True)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place the order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", 1, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", 1, True) # Adj. Close: 127.64
		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000 + (127.64 - 42.09 - 0.5*2))
		self.assertTrue(strat.getOrderUpdatedEvents() == 2)
		# The results are slightly different different only because I'm taking into account the first bar as well,
		# and I'm also adding commissions.
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252), 4) == 0.7763)

	def testSharpeRatioIGE_SPY_Broker(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("sharpe-ratio-test-spy.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.getBroker().setUseAdjustedValues(True)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place IGE order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", 1, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", 1, True) # Adj. Close: 127.64

		# Manually place SPY order to get it filled on the first bar.
		order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL_SHORT, "spy", 1, True) # Adj. Close: 105.52
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, "spy", 1, True) # Adj. Close: 147.67

		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.64 - 42.09) + (105.52 - 147.67), 2))
		self.assertTrue(strat.getOrderUpdatedEvents() == 4)
		# The results are slightly different different only because I'm taking into account the first bar as well.
		# self.assertTrue(round(stratAnalyzer.getSharpeRatio(0, 252), 5) == 0.92742)

def getTestCases():
	ret = []

	ret.append(SharpeRatioTestCase("testNoTrades"))
	ret.append(SharpeRatioTestCase("testIGE_Broker"))
	ret.append(SharpeRatioTestCase("testIGE_Broker2"))
	ret.append(SharpeRatioTestCase("testIGE_BrokerWithCommission"))
	# This testcase is not enabled since I think that the results from the book are not correct.
	# ret.append(SharpeRatioTestCase("testSharpeRatioIGE_SPY_Broker"))

	return ret

