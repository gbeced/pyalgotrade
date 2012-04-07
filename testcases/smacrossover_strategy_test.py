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
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
import common

class SMACrossOverStrategy(strategy.Strategy):
	def __init__(self, feed, fastSMA, slowSMA):
		strategy.Strategy.__init__(self, feed, 1000)
		ds = feed.getDataSeries("orcl").getCloseDataSeries()
		fastSMADS = ma.SMA(ds, fastSMA)
		slowSMADS = ma.SMA(ds, slowSMA)
		self.__crossAbove = cross.CrossAbove(fastSMADS, slowSMADS)
		self.__crossBelow = cross.CrossBelow(fastSMADS, slowSMADS)
		self.__longPos = None
		self.__shortPos = None
		self.__finalValue = None

	def getFinalValue(self):
		return self.__finalValue

	def onEnterCanceled(self, position):
		if position == self.__longPos:
			self.__longPos = None
		elif position == self.__shortPos:
			self.__shortPos = None
		else:
			assert(False)

	def onExitOk(self, position):
		if position == self.__longPos:
			self.__longPos = None
		elif position == self.__shortPos:
			self.__shortPos = None
		else:
			assert(False)

	def onExitCanceled(self, position):
		# If the exit was canceled, re-submit it.
		self.exitPosition(position)

	def onBars(self, bars):
		# Wait for enough bars to be available.
		if self.__crossAbove.getValue() is None or self.__crossBelow.getValue() is None:
			return

		if self.__crossAbove.getValue() == 1:
			assert(self.__longPos == None)
			self.__longPos = self.enterLong("orcl", 10, True)
			if self.__shortPos:
				self.exitPosition(self.__shortPos)
		elif self.__crossBelow.getValue() == 1:
			assert(self.__shortPos == None)
			self.__shortPos = self.enterShort("orcl", 10, True)
			if self.__longPos:
				self.exitPosition(self.__longPos)

	def onFinish(self, bars):
		self.__finalValue = self.getBroker().getValue(bars)

class TestCase(unittest.TestCase):
	def testSMACrossOver(self):
		feed = csvfeed.YahooFeed()
		feed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		myStrategy = SMACrossOverStrategy(feed, 10, 25)
		myStrategy.run()
		# This is the exact same result that we get using NinjaTrader.
		self.assertTrue(round(myStrategy.getFinalValue(), 2) == 977.3)

def getTestCases():
	ret = []
	ret.append(TestCase("testSMACrossOver"))
	return ret

