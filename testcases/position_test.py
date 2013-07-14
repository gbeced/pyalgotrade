# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

import unittest

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
import common

def load_daily_barfeed(instrument):
	barFeed = yahoofeed.Feed()
	barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
	return barFeed

class TestStrategy(strategy.BacktestingStrategy):
	def __init__(self, barFeed, instrument):
		strategy.BacktestingStrategy.__init__(self, barFeed)
		self.instrument = instrument
		self.enterOk = 0
		self.enterCanceled = 0
		self.exitOk = 0
		self.exitCanceled = 0
		self.orderUpdated = 0

	def onOrderUpdated(self, order):
		self.orderUpdated += 1

	def onEnterOk(self, position):
		self.enterOk += 1

	def onEnterCanceled(self, position):
		self.enterCanceled += 1

	def onExitOk(self, position):
		self.exitOk += 1

	def onExitCanceled(self, position):
		self.exitCanceled += 1

class EnterAndExitStrategy(TestStrategy):
	def onStart(self):
		self.position = None

	def onBars(self, bars):
		if self.position == None:
			self.position = self.enterLong(self.instrument, 1)
		elif self.position.entryFilled() and not self.position.exitFilled():
			self.position.exit()

class DoubleExitStrategy(TestStrategy):
	def onStart(self):
		self.position = None
		self.doubleExit = False
		self.doubleExitFailed = False

	def onBars(self, bars):
		if self.position == None:
			self.position = self.enterLong(self.instrument, 1)
		elif not self.doubleExit:
			self.doubleExit = True
			self.position.exit()
			try:
				self.position.exit()
			except Exception:
				self.doubleExitFailed = True

class CancelEntryStrategy(TestStrategy):
	def onStart(self):
		self.position = None

	def onBars(self, bars):
		if self.position == None:
			self.position = self.enterLong(self.instrument, 1)
			self.position.cancelEntry()

class ExitEntryNotFilledStrategy(TestStrategy):
	def onStart(self):
		self.position = None

	def onBars(self, bars):
		if self.position == None:
			self.position = self.enterLong(self.instrument, 1)
			self.position.exit()

class ResubmitExitStrategy(TestStrategy):
	def onStart(self):
		self.position = None
		self.exitRequestCanceled = False

	def onBars(self, bars):
		if self.position == None:
			self.position = self.enterLong(self.instrument, 1)
		elif self.position.entryFilled() and not self.position.exitFilled():
			self.position.exit()
			if not self.exitRequestCanceled:
				self.position.cancelExit()
				self.exitRequestCanceled = True

class TestCase(unittest.TestCase):
	TestInstrument = "doesntmatter"

	def testEnterAndExit(self):
		instrument = "orcl"
		barFeed = load_daily_barfeed(instrument)
		strat = EnterAndExitStrategy(barFeed, instrument)
		strat.run()

		self.assertEqual(strat.enterOk, 1)
		self.assertEqual(strat.enterCanceled, 0)
		self.assertEqual(strat.exitOk, 1)
		self.assertEqual(strat.exitCanceled, 0)
		self.assertEqual(strat.orderUpdated, 0)
		self.assertEqual(len(strat.getActivePositions()), 0)
		self.assertEqual(len(strat.getOrderToPosition()), 0)

	def testCancelEntry(self):
		instrument = "orcl"
		barFeed = load_daily_barfeed(instrument)
		strat = CancelEntryStrategy(barFeed, instrument)
		strat.run()

		self.assertEqual(strat.enterOk, 0)
		self.assertEqual(strat.enterCanceled, 1)
		self.assertEqual(strat.exitOk, 0)
		self.assertEqual(strat.exitCanceled, 0)
		self.assertEqual(strat.orderUpdated, 0)
		self.assertEqual(len(strat.getActivePositions()), 0)
		self.assertEqual(len(strat.getOrderToPosition()), 0)

	def testExitEntryNotFilled(self):
		instrument = "orcl"
		barFeed = load_daily_barfeed(instrument)
		strat = ExitEntryNotFilledStrategy(barFeed, instrument)
		strat.run()

		self.assertEqual(strat.enterOk, 0)
		self.assertEqual(strat.enterCanceled, 1)
		self.assertEqual(strat.exitOk, 0)
		self.assertEqual(strat.exitCanceled, 0)
		self.assertEqual(strat.orderUpdated, 0)
		self.assertEqual(len(strat.getActivePositions()), 0)
		self.assertEqual(len(strat.getOrderToPosition()), 0)

	def testDoubleExitFails(self):
		instrument = "orcl"
		barFeed = load_daily_barfeed(instrument)
		strat = DoubleExitStrategy(barFeed, instrument)
		strat.run()

		self.assertEqual(strat.enterOk, 1)
		self.assertEqual(strat.enterCanceled, 0)
		self.assertEqual(strat.exitOk, 1)
		self.assertEqual(strat.exitCanceled, 0)
		self.assertEqual(strat.orderUpdated, 0)
		self.assertEqual(strat.doubleExit, True)
		self.assertEqual(strat.doubleExitFailed, True)
		self.assertEqual(len(strat.getActivePositions()), 0)
		self.assertEqual(len(strat.getOrderToPosition()), 0)

	def testResubmitExit(self):
		instrument = "orcl"
		barFeed = load_daily_barfeed(instrument)
		strat = ResubmitExitStrategy(barFeed, instrument)
		strat.run()

		self.assertEqual(strat.enterOk, 1)
		self.assertEqual(strat.enterCanceled, 0)
		self.assertEqual(strat.exitOk, 1)
		self.assertEqual(strat.exitCanceled, 1)
		self.assertEqual(strat.orderUpdated, 0)
		self.assertEqual(len(strat.getActivePositions()), 0)
		self.assertEqual(len(strat.getOrderToPosition()), 0)

def getTestCases(includeExternal = True):
	ret = []

	ret.append(TestCase("testEnterAndExit"))
	ret.append(TestCase("testCancelEntry"))
	ret.append(TestCase("testExitEntryNotFilled"))
	ret.append(TestCase("testDoubleExitFails"))
	ret.append(TestCase("testResubmitExit"))

	return ret

