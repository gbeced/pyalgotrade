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

from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.stratanalyzer import trades
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade import broker

import strategy_test
import common

import unittest
import datetime
import math

class StratAnalyzerTestCase(unittest.TestCase):
	TestInstrument = "spy"

	def __createStrategy(self):
		barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		barFilter = csvfeed.USEquitiesRTH()
		barFeed.setBarFilter(barFilter)
		barFeed.addBarsFromCSV(StratAnalyzerTestCase.TestInstrument, common.get_data_file_path("nt-spy-minute-2011.csv"))
		return strategy_test.TestStrategy(barFeed, 1000)

	def testBasicAnalyzer(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.BasicAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)

		# Winning trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 0), strat.enterLong, StratAnalyzerTestCase.TestInstrument, 1) # 127.14
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 16), strat.exitPosition) # 127.16
		# Losing trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 30), strat.enterLong, StratAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 31), strat.exitPosition) # 127.16
		# Winning trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 38), strat.enterLong, StratAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 42), strat.exitPosition) # 127.26
		# Unfinished trade not closed
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 47), strat.enterLong, StratAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2) + (127.26 - 127.16) - 127.34, 2))

		self.assertTrue(stratAnalyzer.getCount() == 3)
		self.assertTrue(round(stratAnalyzer.getMean(), 2) == 0.03)
		self.assertTrue(round(stratAnalyzer.getStdDev(), 2) == 0.07)
		self.assertTrue(round(stratAnalyzer.getStdDev(0), 2) == 0.06)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(stratAnalyzer.getWinningCount() == 2)
		self.assertTrue(round(stratAnalyzer.getWinningMean(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(0), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getLosingCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosingMean(), 2) == -0.04)
		self.assertTrue(math.isnan(stratAnalyzer.getLosingStdDev()))
		self.assertTrue(stratAnalyzer.getLosingStdDev(0) == 0)

	def testSharpeRatioIGE(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually open the postion to enter on the first bar.
		strat.enterLong("ige", 1, True) # 91.01
		strat.addPosExit(datetime.datetime(2007, 11, 13), strat.exitPosition) # 129.32
		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000 + (129.32 - 91.01))
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252), 4) == 0.7893)
		self.assertTrue(strat.getOrderUpdatedEvents() == 0)

	def testSharpeRatioIGE_Broker(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place the order to get it filled on the first bar.
		strat.getBroker().setUseAdjustedValues(True)
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", 1, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", 1, True) # Adj. Close: 127.64
		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000 + (127.64 - 42.09))
		self.assertTrue(strat.getOrderUpdatedEvents() == 2)
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252), 4) == 0.7893)

	def testSharpeRatioIGE_SPY_Broker(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("sharpe-ratio-test-spy.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		# Manually place IGE order to get it filled on the first bar.
		strat.getBroker().setUseAdjustedValues(True)
		order = strat.getBroker().createMarketOrder(broker.Order.Action.BUY, "ige", 1, True) # Adj. Close: 42.09
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, "ige", 1, True) # Adj. Close: 127.64

		# Manually place SPY order to get it filled on the first bar.
		strat.getBroker().setUseAdjustedValues(True)
		order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL_SHORT, "spy", 1, True) # Adj. Close: 105.52
		order.setGoodTillCanceled(True)
		strat.getBroker().placeOrder(order)
		strat.addOrder(datetime.datetime(2007, 11, 13), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, "spy", 1, True) # Adj. Close: 147.67

		strat.run()
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.64 - 42.09) + (105.52 - 147.67), 2))
		self.assertTrue(strat.getOrderUpdatedEvents() == 4)
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0, 252), 5) == 0.78368)

def getTestCases():
	ret = []
	ret.append(StratAnalyzerTestCase("testBasicAnalyzer"))
	ret.append(StratAnalyzerTestCase("testSharpeRatioIGE"))
	ret.append(StratAnalyzerTestCase("testSharpeRatioIGE_Broker"))
	ret.append(StratAnalyzerTestCase("testSharpeRatioIGE_SPY_Broker"))
	return ret

