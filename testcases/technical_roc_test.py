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
from pyalgotrade.technical import roc
from pyalgotrade import dataseries

class ROCTestCase(unittest.TestCase):
	def __buildROC(self, values, period):
		return roc.RateOfChange(dataseries.SequenceDataSeries(values), period)

	def testPeriod12(self):
		# http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:rate_of_change
		inputValues = [ 11045.27, 11167.32, 11008.61, 11151.83, 10926.77, 10868.12, 10520.32, 10380.43, 10785.14, 10748.26, 10896.91, 10782.95, 10620.16, 10625.83, 10510.95, 10444.37, 10068.01, 10193.39, 10066.57, 10043.75]
		roc_ = self.__buildROC(inputValues, 12)
		outputValues = [-3.85, -4.85, -4.52, -6.34, -7.86, -6.21, -4.31, -3.24]
		for i in range(len(outputValues)):
			outputValue = roc_[12 + i]
			self.assertTrue(round(outputValue, 2) == outputValues[i])

		self.assertEqual(len(roc_.getDateTimes()), len(inputValues))
		for i in range(len(roc_)):
			self.assertEqual(roc_.getDateTimes()[i], None)

	def testPeriod1(self):
		def simple_roc(value1, value2):
			return self.__buildROC([value1, value2], 1)[1]

		self.assertTrue(simple_roc(1, 2) == 100)
		self.assertTrue(simple_roc(1, 2) == simple_roc(50, 100))
		self.assertTrue(simple_roc(2, 1) == -50)
		self.assertTrue(simple_roc(2, 1) == simple_roc(100, 50))

def getTestCases():
	ret = []
	ret.append(ROCTestCase("testPeriod12"))
	ret.append(ROCTestCase("testPeriod1"))
	return ret

