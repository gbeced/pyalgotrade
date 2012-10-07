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
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.stratanalyzer import trades
from pyalgotrade import broker

import strategy_test
import common

import unittest
import datetime
import math

class TradesAnalyzerTestCase(unittest.TestCase):
	TestInstrument = "spy"

	def __createStrategy(self):
		barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		barFilter = csvfeed.USEquitiesRTH()
		barFeed.setBarFilter(barFilter)
		barFeed.addBarsFromCSV(TradesAnalyzerTestCase.TestInstrument, common.get_data_file_path("nt-spy-minute-2011.csv"))
		return strategy_test.TestStrategy(barFeed, 1000)

	def testNoTrades(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.BasicAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)

		strat.run()

		self.assertTrue(strat.getBroker().getCash() == 1000)

		self.assertTrue(stratAnalyzer.getCount() == 0)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(stratAnalyzer.getMean() == None)
		self.assertTrue(stratAnalyzer.getStdDev() == None)
		self.assertTrue(stratAnalyzer.getStdDev(0) == None)

		self.assertTrue(stratAnalyzer.getWinningCount() == 0)
		self.assertTrue(stratAnalyzer.getWinningMean() == None)
		self.assertTrue(stratAnalyzer.getWinningStdDev() == None)
		self.assertTrue(stratAnalyzer.getWinningStdDev(0) == None)

		self.assertTrue(stratAnalyzer.getLosingCount() == 0)
		self.assertTrue(stratAnalyzer.getLosingMean() == None)
		self.assertTrue(stratAnalyzer.getLosingStdDev() == None)
		self.assertTrue(stratAnalyzer.getLosingStdDev(0) == None)

	def testSomeTrades(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.BasicAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)

		# Winning trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 0), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 16), strat.exitPosition) # 127.16
		# Losing trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 30), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 31), strat.exitPosition) # 127.16
		# Winning trade
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 38), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addPosExit(datetime.datetime(2011, 1, 3, 15, 42), strat.exitPosition) # 127.26
		# Unfinished trade not closed
		strat.addPosEntry(datetime.datetime(2011, 1, 3, 15, 47), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2) + (127.26 - 127.16) - 127.34, 2))

		self.assertTrue(stratAnalyzer.getCount() == 3)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(round(stratAnalyzer.getMean(), 2) == 0.03)
		self.assertTrue(round(stratAnalyzer.getStdDev(), 2) == 0.07)
		self.assertTrue(round(stratAnalyzer.getStdDev(0), 2) == 0.06)

		self.assertTrue(stratAnalyzer.getWinningCount() == 2)
		self.assertTrue(round(stratAnalyzer.getWinningMean(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(0), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getLosingCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosingMean(), 2) == -0.04)
		self.assertTrue(math.isnan(stratAnalyzer.getLosingStdDev()))
		self.assertTrue(stratAnalyzer.getLosingStdDev(0) == 0)

	def testSomeTrades_Broker(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.BasicAnalyzer()
		strat.attachAnalyzer(stratAnalyzer)

		# Winning trade
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Losing trade
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 31), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Winning trade
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 38), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 42), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.26
		# Open trade.
		strat.addOrder(datetime.datetime(2011, 1, 3, 15, 47), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2) + (127.26 - 127.16) - 127.34, 2))

		self.assertTrue(stratAnalyzer.getCount() == 3)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(round(stratAnalyzer.getMean(), 2) == 0.03)
		self.assertTrue(round(stratAnalyzer.getStdDev(), 2) == 0.07)
		self.assertTrue(round(stratAnalyzer.getStdDev(0), 2) == 0.06)

		self.assertTrue(stratAnalyzer.getWinningCount() == 2)
		self.assertTrue(round(stratAnalyzer.getWinningMean(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getWinningStdDev(0), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getLosingCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosingMean(), 2) == -0.04)
		self.assertTrue(math.isnan(stratAnalyzer.getLosingStdDev()))
		self.assertTrue(stratAnalyzer.getLosingStdDev(0) == 0)

def getTestCases():
	ret = []

	ret.append(TradesAnalyzerTestCase("testNoTrades"))
	ret.append(TradesAnalyzerTestCase("testSomeTrades"))
	ret.append(TradesAnalyzerTestCase("testSomeTrades_Broker"))

	return ret

