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
from pyalgotrade.technical import rsi
from pyalgotrade import dataseries

class TestCase(unittest.TestCase):
	def testAvgGainLoss(self):
		# We divide by 2 because N samples yield N-1 averages.

		# Gain only
		avgGain, avgLoss = rsi.avg_gain_loss([1, 2, 3])
		self.assertTrue(avgGain == 2 / float(2))
		self.assertTrue(avgLoss == 0)

		# Loss only
		avgGain, avgLoss = rsi.avg_gain_loss([3, 2, 1])
		self.assertTrue(avgGain == 0)
		self.assertTrue(avgLoss == 2 / float(2))

		# Gain and Loss equal
		avgGain, avgLoss = rsi.avg_gain_loss([1, 0, 1])
		self.assertTrue(avgGain == 1 / float(2))
		self.assertTrue(avgLoss == 1 / float(2))

		# Gain and Loss different
		avgGain, avgLoss = rsi.avg_gain_loss([1, 3, 2])
		self.assertTrue(avgGain == 2 / float(2))
		self.assertTrue(avgLoss == 1 / float(2))

	def __buildRSI(self, values, period):
		return rsi.RSI(dataseries.SequenceDataSeries(values), period)

	def testStockChartsRSI(self):
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_in
		common.test_from_csv(self, "rsi-test.csv", lambda inputDS: rsi.RSI(inputDS, 14), 3)

	def testStockChartsRSI_Reverse(self):
		# Test in reverse order to trigger recursive calls.
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_in
		common.test_from_csv(self, "rsi-test.csv", lambda inputDS: rsi.RSI(inputDS, 14), 3, True)

	def testDateTimes(self):
		rsi = self.__buildRSI(range(10), 3)

		self.assertEqual(len(rsi.getDateTimes()), 10)
		for i in range(len(rsi)):
			self.assertEqual(rsi.getDateTimes()[i], None)

def getTestCases():
	ret = []
	ret.append(TestCase("testAvgGainLoss"))
	ret.append(TestCase("testStockChartsRSI"))
	ret.append(TestCase("testStockChartsRSI_Reverse"))
	ret.append(TestCase("testDateTimes"))
	return ret

