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

import unittest
import datetime
from pyalgotrade.technical import stoch
from pyalgotrade import dataseries
from pyalgotrade import bar

def values_equal(v1, v2):
	if v1 != None and v2 != None:
		return round(v1, 3) == round(v2, 3)
	elif v1 == None and v2 == None:
		return True
	return False

class TestCase(unittest.TestCase):
	def setUp(self):
		self.__currSeconds = 0

	def __buildBar(self, openPrice, highPrice, lowPrice, closePrice):
		dateTime = datetime.datetime.now() + datetime.timedelta(seconds=self.__currSeconds)
		self.__currSeconds += 1
		return bar.Bar(dateTime, openPrice, highPrice, lowPrice, closePrice, closePrice*10, closePrice)

	def __buildBarDataSeries(self, closePrices, highPrices, lowPrices):
		assert(len(closePrices) == len(highPrices) == len(lowPrices))
		ret = dataseries.BarDataSeries()
		for i in range(len(highPrices)):
			ret.appendValue( self.__buildBar(closePrices[i], highPrices[i], lowPrices[i], closePrices[i]) )
		return ret

	def testShortPeriod(self):
		highPrices = [3, 3, 3]
		lowPrices = [1, 1, 1]
		closePrices = [2, 2, 3]

		stochFilter = stoch.StochasticOscillator(self.__buildBarDataSeries(closePrices, highPrices, lowPrices), 2, 2)
		self.assertTrue( values_equal(stochFilter[0], None) )
		self.assertTrue( values_equal(stochFilter[1], 50) )
		self.assertTrue( values_equal(stochFilter[2], 100) )

		self.assertTrue( values_equal(stochFilter.getD()[0], None) )
		self.assertTrue( values_equal(stochFilter.getD()[1], None) )
		self.assertTrue( values_equal(stochFilter.getD()[2], 75) )

		self.assertEqual(len(stochFilter.getDateTimes()), len(closePrices))
		for i in range(len(stochFilter)):
			self.assertNotEqual(stochFilter.getDateTimes()[i], None)

	def testStockChartsStoch(self):
		# Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:stochastic_oscillato
		highPrices = [127.0090, 127.6159, 126.5911, 127.3472, 128.1730, 128.4317, 127.3671, 126.4220, 126.8995, 126.8498, 125.6460, 125.7156, 127.1582, 127.7154, 127.6855, 128.2228, 128.2725, 128.0934, 128.2725, 127.7353, 128.7700, 129.2873, 130.0633, 129.1182, 129.2873, 128.4715, 128.0934, 128.6506, 129.1381, 128.6406]
		lowPrices = [125.3574, 126.1633, 124.9296, 126.0937, 126.8199, 126.4817, 126.0340, 124.8301, 126.3921, 125.7156, 124.5615, 124.5715, 125.0689, 126.8597, 126.6309, 126.8001, 126.7105, 126.8001, 126.1335, 125.9245, 126.9891, 127.8148, 128.4715, 128.0641, 127.6059, 127.5960, 126.9990, 126.8995, 127.4865, 127.3970]
		closePrices = lowPrices[:13] # To keep initial close prince between low/high
		closePrices.extend([127.2876, 127.1781, 128.0138, 127.1085, 127.7253, 127.0587, 127.3273, 128.7103, 127.8745, 128.5809, 128.6008, 127.9342, 128.1133, 127.5960, 127.5960, 128.6904, 128.2725])
		kValues = [None, None, None, None, None, None, None, None, None, None, None, None, None, 70.4382, 67.6089, 89.2021, 65.8106, 81.7477, 64.5238, 74.5298, 98.5814, 70.1045, 73.0561, 73.4178, 61.2313, 60.9563, 40.3861, 40.3861, 66.8285, 56.7314]
		dValues = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 75.7497, 74.2072, 78.9201, 70.6940, 73.6004, 79.2117, 81.0719, 80.5807, 72.1928, 69.2351, 65.2018, 54.1912, 47.2428, 49.2003, 54.6487]

		stochFilter = stoch.StochasticOscillator(self.__buildBarDataSeries(closePrices, highPrices, lowPrices), 14)
		for i in range(len(kValues)):
			self.assertTrue( values_equal(stochFilter[i], kValues[i]) )
			self.assertTrue( values_equal(stochFilter.getD()[i], dValues[i]) )

		self.assertEqual(len(stochFilter.getDateTimes()), len(closePrices))
		for i in range(len(stochFilter)):
			self.assertNotEqual(stochFilter.getDateTimes()[i], None)

def getTestCases():
	ret = []
	ret.append(TestCase("testShortPeriod"))
	ret.append(TestCase("testStockChartsStoch"))
	return ret

