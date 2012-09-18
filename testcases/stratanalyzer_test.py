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
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import returns
from pyalgotrade import broker

import strategy_test
import common

import unittest
import datetime
import math

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
		order = strat.getBroker().createMarketOrder(broker.Order.Action.SELL, ReturnsTestCase.TestInstrument, 1, True) # Open: 15.91
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

class SharpeRatioTestCase(unittest.TestCase):
	def testNoTrades(self):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		stratAnalyzer = sharpe.SharpeRatio()
		strat.attachAnalyzer(stratAnalyzer)

		strat.run()
		self.assertTrue(strat.getBroker().getCash() == 1000)
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0.04, 252) / 10**14, 4) == -7.204)
		self.assertTrue(stratAnalyzer.getSharpeRatio(0, 252) == None)
	
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
		self.assertTrue(round(stratAnalyzer.getSharpeRatio(0, 252), 5) == 0.78368)

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

	def testDrawDownIGE_Broker(self):
		# This testcase is based on an example from Ernie Chan's book:
		# 'Quantitative Trading: How to Build Your Own Algorithmic Trading Business'
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV("ige", common.get_data_file_path("sharpe-ratio-test-ige.csv"))
		barFeed.addBarsFromCSV("spy", common.get_data_file_path("sharpe-ratio-test-spy.csv"))
		strat = strategy_test.TestStrategy(barFeed, 1000)
		strat.getBroker().setUseAdjustedValues(True)
		strat.setBrokerOrdersGTC(True)
		stratAnalyzer = drawdown.DrawDown()
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
		self.assertTrue(round(stratAnalyzer.getMaxDrawDown(), 5) == 0.09529)
		self.assertTrue(stratAnalyzer.getMaxDrawDownDuration()== 497)

def getTestCases():
	ret = []

	ret.append(ReturnsTestCase("testOneBarReturn"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_OpenClose"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseOpen"))
	ret.append(ReturnsTestCase("testTwoBarReturns_CloseClose"))

	ret.append(TradesAnalyzerTestCase("testNoTrades"))
	ret.append(TradesAnalyzerTestCase("testSomeTrades"))

	ret.append(SharpeRatioTestCase("testNoTrades"))
	ret.append(SharpeRatioTestCase("testSharpeRatioIGE"))
	ret.append(SharpeRatioTestCase("testSharpeRatioIGE_Broker"))
	ret.append(SharpeRatioTestCase("testSharpeRatioIGE_SPY_Broker"))

	ret.append(DrawDownTestCase("testNoTrades"))
	ret.append(DrawDownTestCase("testDrawDownIGE_Broker"))

	return ret

