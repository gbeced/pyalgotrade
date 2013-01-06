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
from pyalgotrade.broker import backtesting

import strategy_test
import common

import unittest
import datetime
import math
from distutils import version
import pytz
import numpy

def buildUTCDateTime(year, month, day, hour, minute):
	ret = datetime.datetime(year, month, day, hour, minute)
	ret = pytz.utc.localize(ret)
	return ret

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
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		strat.run()

		self.assertTrue(strat.getBroker().getCash() == 1000)

		self.assertTrue(stratAnalyzer.getCount() == 0)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(stratAnalyzer.getProfitableCount() == 0)
		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 0)

	def testSomeTrades_Position(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Winning trade
		strat.addPosEntry(buildUTCDateTime(2011, 1, 3, 15, 0), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		strat.addPosExit(buildUTCDateTime(2011, 1, 3, 15, 16), strat.exitPosition) # 127.16
		# Losing trade
		strat.addPosEntry(buildUTCDateTime(2011, 1, 3, 15, 30), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addPosExit(buildUTCDateTime(2011, 1, 3, 15, 31), strat.exitPosition) # 127.16
		# Winning trade
		strat.addPosEntry(buildUTCDateTime(2011, 1, 3, 15, 38), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addPosExit(buildUTCDateTime(2011, 1, 3, 15, 42), strat.exitPosition) # 127.26
		# Unfinished trade not closed
		strat.addPosEntry(buildUTCDateTime(2011, 1, 3, 15, 47), strat.enterLong, TradesAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2) + (127.26 - 127.16) - 127.34, 2))

		self.assertTrue(stratAnalyzer.getCount() == 3)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.03)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 2) == 0.07)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=0), 2) == 0.06)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 2)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getProfits().std(ddof=1), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getProfits().std(ddof=0), 2) == 0.04)
		self.assertEqual(stratAnalyzer.getPositiveReturns()[0], (127.16 - 127.14) / 127.14)
		self.assertEqual(stratAnalyzer.getPositiveReturns()[1], (127.26 - 127.16) / 127.16)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.04)
		if version.LooseVersion(numpy.__version__) >= version.LooseVersion("1.6.2"):
			self.assertTrue(math.isnan(stratAnalyzer.getLosses().std(ddof=1)))
		else:
			self.assertTrue(stratAnalyzer.getLosses().std(ddof=1) == 0)
		self.assertTrue(stratAnalyzer.getLosses().std(ddof=0) == 0)
		self.assertEqual(stratAnalyzer.getNegativeReturns()[0], (127.16 - 127.2) / 127.2)

	def testSomeTrades(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Winning trade
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Losing trade
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 31), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Winning trade
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 38), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 42), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.26
		# Open trade.
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 47), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2) + (127.26 - 127.16) - 127.34, 2))

		self.assertTrue(stratAnalyzer.getCount() == 3)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)
		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.03)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 2) == 0.07)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=0), 2) == 0.06)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 2)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getProfits().std(ddof=1), 2) == 0.06)
		self.assertTrue(round(stratAnalyzer.getProfits().std(ddof=0), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.04)
		if version.LooseVersion(numpy.__version__) >= version.LooseVersion("1.6.2"):
			self.assertTrue(math.isnan(stratAnalyzer.getLosses().std(ddof=1)))
		else:
			self.assertTrue(stratAnalyzer.getLosses().std(ddof=1) == 0)
		self.assertTrue(stratAnalyzer.getLosses().std(ddof=0) == 0)

	def testSomeTradesWithCommissions(self):
		strat = self.__createStrategy()
		strat.getBroker().setCommission(backtesting.FixedCommission(0.01))
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Losing trade
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 31), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Winning trade
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 38), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 42), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.26
		# Open trade.
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 47), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.34
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.2) + (127.26 - 127.16) - 127.34 - 0.01*5, 2))
		self.assertTrue(numpy.array_equal(stratAnalyzer.getCommissionsForAllTrades(), numpy.array([0.02, 0.02])))
		self.assertTrue(numpy.array_equal(stratAnalyzer.getCommissionsForProfitableTrades(), numpy.array([0.02])))
		self.assertTrue(numpy.array_equal(stratAnalyzer.getCommissionsForUnprofitableTrades(), numpy.array([0.02])))
		self.assertTrue(numpy.array_equal(stratAnalyzer.getCommissionsForEvenTrades(), numpy.array([])))

	def testLongShort(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Exit long and enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 2) # 127.16
		# Exit short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2), 2))

		self.assertTrue(stratAnalyzer.getCount() == 2)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == -0.01)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 4) == 0.0424)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.02)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.04)

	def testLongShort2(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Exit long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.16 - 127.14) + (127.16 - 127.2), 2))

		self.assertTrue(stratAnalyzer.getCount() == 2)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == -0.01)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 4) == 0.0424)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.02)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.04)

	def testShortLong(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Exit short and enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 2) # 127.16
		# Exit long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.14 - 127.16) + (127.2 - 127.16), 2))

		self.assertTrue(stratAnalyzer.getCount() == 2)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.01)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 4) == 0.0424)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.02)

	def testShortLong2(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Exit short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.14 - 127.16) + (127.2 - 127.16), 2))

		self.assertTrue(stratAnalyzer.getCount() == 2)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.01)
		self.assertTrue(round(stratAnalyzer.getAll().std(ddof=1), 4) == 0.0424)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.04)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.02)

	def testLong2(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Extend long position
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 2) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.2 - 127.14) + (127.2 - 127.16), 2))

		self.assertTrue(stratAnalyzer.getCount() == 1)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.1)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.1)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 0)

	def testLong3(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.BUY, TradesAnalyzerTestCase.TestInstrument, 2) # 127.14
		# Decrease long position
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit long
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.SELL, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.2 - 127.14) + (127.16 - 127.14), 2))

		self.assertTrue(stratAnalyzer.getCount() == 1)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == 0.08)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getProfits().mean(), 2) == 0.08)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 0)

	def testShort2(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 1) # 127.14
		# Extend short position
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 2) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.14 - 127.2) + (127.16 - 127.2), 2))

		self.assertTrue(stratAnalyzer.getCount() == 1)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == -0.1)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.1)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 0)

	def testShort3(self):
		strat = self.__createStrategy()
		stratAnalyzer = trades.Trades()
		strat.attachAnalyzer(stratAnalyzer)

		# Enter short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 0), strat.getBroker().createMarketOrder, broker.Order.Action.SELL_SHORT, TradesAnalyzerTestCase.TestInstrument, 2) # 127.14
		# Decrease short position
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 16), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 1) # 127.16
		# Exit short
		strat.addOrder(buildUTCDateTime(2011, 1, 3, 15, 30), strat.getBroker().createMarketOrder, broker.Order.Action.BUY_TO_COVER, TradesAnalyzerTestCase.TestInstrument, 1) # 127.2
		strat.run()

		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.14 - 127.16) + (127.14 - 127.2), 2))

		self.assertTrue(stratAnalyzer.getCount() == 1)
		self.assertTrue(stratAnalyzer.getEvenCount() == 0)

		self.assertTrue(round(stratAnalyzer.getAll().mean(), 2) == -0.08)

		self.assertTrue(stratAnalyzer.getUnprofitableCount() == 1)
		self.assertTrue(round(stratAnalyzer.getLosses().mean(), 2) == -0.08)

		self.assertTrue(stratAnalyzer.getProfitableCount() == 0)

def getTestCases():
	ret = []

	ret.append(TradesAnalyzerTestCase("testNoTrades"))
	ret.append(TradesAnalyzerTestCase("testSomeTrades_Position"))
	ret.append(TradesAnalyzerTestCase("testSomeTrades"))
	ret.append(TradesAnalyzerTestCase("testSomeTradesWithCommissions"))
	ret.append(TradesAnalyzerTestCase("testLong2"))
	ret.append(TradesAnalyzerTestCase("testLong3"))
	ret.append(TradesAnalyzerTestCase("testLongShort"))
	ret.append(TradesAnalyzerTestCase("testLongShort2"))
	ret.append(TradesAnalyzerTestCase("testShort2"))
	ret.append(TradesAnalyzerTestCase("testShort3"))
	ret.append(TradesAnalyzerTestCase("testShortLong"))
	ret.append(TradesAnalyzerTestCase("testShortLong2"))

	return ret

