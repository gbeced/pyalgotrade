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
from pyalgotrade.technical import trend
from pyalgotrade import dataseries

class SlopeTest(unittest.TestCase):
	def __buildSlope(self, values, period):
		seqDS = dataseries.SequenceDataSeries()
		ret = trend.Slope(seqDS, period)
		for value in values:
			seqDS.append(value)
		return ret

	def testSlope(self):
		slope = self.__buildSlope([1, 2, 3, 2, 1], 3)
		self.assertEqual(slope[0], None)
		self.assertEqual(slope[1], None)
		self.assertEqual(slope[2], 1.0)
		self.assertEqual(slope[3], 0.0)
		self.assertEqual(slope[4], -1.0)

class TrendTest(unittest.TestCase):
	def __buildTrend(self, values, trendDays, positiveThreshold, negativeThreshold):
		seqDS = dataseries.SequenceDataSeries()
		ret = trend.Trend(seqDS, trendDays, positiveThreshold, negativeThreshold)
		for value in values:
			seqDS.append(value)
		return ret

	def testTrend(self):
		trend = self.__buildTrend([1, 2, 3, 2, 1], 3, 0, 0)
		self.assertTrue(trend[0] == None)
		self.assertTrue(trend[1] == None)
		self.assertTrue(trend[2] == True)
		self.assertTrue(trend[3] == None)
		self.assertTrue(trend[4] == False)

		self.assertEqual(len(trend.getDateTimes()), 5)
		for i in range(len(trend)):
			self.assertEqual(trend.getDateTimes()[i], None)

	def testTrendWithCustomThresholds(self):
		trend = self.__buildTrend([1, 2, 3, 5, -10], 3, 1, -1)
		self.assertTrue(trend[0] == None)
		self.assertTrue(trend[1] == None)
		self.assertTrue(trend[2] == None)
		self.assertTrue(trend[3] == True)
		self.assertTrue(trend[4] == False)

		self.assertEqual(len(trend.getDateTimes()), 5)
		for i in range(len(trend)):
			self.assertEqual(trend.getDateTimes()[i], None)

def getTestCases():
	ret = []

	ret.append(SlopeTest("testSlope"))

	ret.append(TrendTest("testTrend"))
	ret.append(TrendTest("testTrendWithCustomThresholds"))

	return ret

