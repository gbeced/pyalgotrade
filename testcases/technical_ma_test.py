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
import common
from pyalgotrade.technical import ma
from pyalgotrade import dataseries

class SMATestCase(unittest.TestCase):
	def __buildSMA(self, period, values):
		return ma.SMA(dataseries.SequenceDataSeries(values), period)

	def testPeriod1(self):
		sma = self.__buildSMA(1, [10, 20])
		self.assertTrue(sma.getValueAbsolute(-1) == None)
		self.assertTrue(sma.getValueAbsolute(0) == 10)
		self.assertTrue(sma.getValueAbsolute(1) == 20)
		self.assertTrue(sma.getValueAbsolute(2) == None)

		self.assertTrue(sma.getValue(-1) == None)
		self.assertTrue(sma.getValue() == 20)
		self.assertTrue(sma.getValue(1) == 10)
		self.assertTrue(sma.getValue(2) == None)

	def testPeriod2(self):
		sma = self.__buildSMA(2, [0, 1, 2])
		self.assertTrue(sma.getValueAbsolute(0) == None)
		self.assertTrue(sma.getValueAbsolute(1) == (0+1) / float(2))
		self.assertTrue(sma.getValueAbsolute(2) == (1+2) / float(2))
		self.assertTrue(sma.getValueAbsolute(3) == None)

		self.assertTrue(sma.getValueAbsolute(2) == sma.getValue())
		self.assertTrue(sma.getValueAbsolute(1) == sma.getValue(1))
		self.assertTrue(sma.getValueAbsolute(0) == sma.getValue(2))

	def testMultipleValues(self):
		period = 5
		values = range(1, 10)
		sma = self.__buildSMA(period, values)
		for i in xrange(period-1, len(values)):
			expected = sum(values[i-(period-1):i+1]) / float(period)
			self.assertTrue(sma.getValueAbsolute(i) == expected)

	def testMultipleValuesSkippingOne(self):
		# Test SMA invalidating fast sma calculation.
		period = 5
		values = range(1, 10)
		sma = self.__buildSMA(period, values)
		for i in xrange(period-1, len(values), 2):
			expected = sum(values[i-(period-1):i+1]) / float(period)
			self.assertTrue(sma.getValueAbsolute(i) == expected)

	def testStockChartsSMA(self):
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
		common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10))

	def testNinjaTraderSMA(self):
		common.test_from_csv(self, "nt-sma-15.csv", lambda inputDS: ma.SMA(inputDS, 15), 3)

class WMATestCase(unittest.TestCase):
	def __buildWMA(self, weights, values):
		from pyalgotrade import dataseries
		return ma.WMA(dataseries.SequenceDataSeries(values), weights)

	def testPeriod1(self):
		sma = self.__buildWMA([2], [10, 20])
		self.assertTrue(sma.getValueAbsolute(0) == 10)
		self.assertTrue(sma.getValueAbsolute(1) == 20)

	def testPeriod2(self):
		weights = [3, 2, 1]
		values = [1, 2, 3]

		wma = self.__buildWMA(weights, values)
		self.assertTrue(wma.getValueAbsolute(0) == None)
		self.assertTrue(wma.getValueAbsolute(1) == None)
		self.assertTrue(wma.getValueAbsolute(2) == (1*3 + 2*2 + 3*1) / float(3+2+1))

class EMATestCase(unittest.TestCase):
	def testStockChartsEMA(self):
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
		common.test_from_csv(self, "sc-ema-10.csv", lambda inputDS: ma.EMA(inputDS, 10), 3)

	def testStockChartsEMA_Reverse(self):
		# Test in reverse order to trigger recursive calls.
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
		common.test_from_csv(self, "sc-ema-10.csv", lambda inputDS: ma.EMA(inputDS, 10), 3, True)

def getTestCases():
	ret = []
	ret.append(SMATestCase("testPeriod1"))
	ret.append(SMATestCase("testPeriod2"))
	ret.append(SMATestCase("testMultipleValues"))
	ret.append(SMATestCase("testStockChartsSMA"))
	ret.append(SMATestCase("testMultipleValuesSkippingOne"))
	ret.append(SMATestCase("testNinjaTraderSMA"))

	ret.append(WMATestCase("testPeriod1"))
	ret.append(WMATestCase("testPeriod2"))

	ret.append(EMATestCase("testStockChartsEMA"))
	ret.append(EMATestCase("testStockChartsEMA_Reverse"))
	return ret

