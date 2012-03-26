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

class TestCase(unittest.TestCase):
	def __buildTrend(self, values, trendDays, positiveThreshold, negativeThreshold):
		return trend.Trend(dataseries.SequenceDataSeries(values), trendDays, positiveThreshold, negativeThreshold)

	def testTrend(self):
		trend = self.__buildTrend([1, 2, 3, 2, 1], 3, 0, 0)
		self.assertTrue(trend.getValueAbsolute(0) == None)
		self.assertTrue(trend.getValueAbsolute(1) == None)
		self.assertTrue(trend.getValueAbsolute(2) == True)
		self.assertTrue(trend.getValueAbsolute(3) == None)
		self.assertTrue(trend.getValueAbsolute(4) == False)

	def testTrendWithCustomThresholds(self):
		trend = self.__buildTrend([1, 2, 3, 5, -10], 3, 1, -1)
		self.assertTrue(trend.getValueAbsolute(0) == None)
		self.assertTrue(trend.getValueAbsolute(1) == None)
		self.assertTrue(trend.getValueAbsolute(2) == None)
		self.assertTrue(trend.getValueAbsolute(3) == True)
		self.assertTrue(trend.getValueAbsolute(4) == False)

def getTestCases():
	ret = []
	ret.append(TestCase("testTrend"))
	ret.append(TestCase("testTrendWithCustomThresholds"))
	return ret

