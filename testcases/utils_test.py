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

from pyalgotrade.utils import stats

import unittest
import math

class StatsTestCase(unittest.TestCase):
	def __assertEqFloat(self, v1, v2):
		if v1 != None and v2 != None:
			# Assume that both are floats.
			if math.isnan(v1) and math.isnan(v2):
				# self.assertEqual will fail if both are nan.
				pass
			else:
				precision = 5
				self.assertEqual(round(v1, precision), round(v2, precision))
		else:
			self.assertEqual(v1, v2)

	def __testMeanImpl(self, values):
		self.__assertEqFloat(stats.mean(values), stats.py_mean(values))

	def __testStdDevImpl(self, values, ddof):
		self.__assertEqFloat(stats.stddev(values, ddof), stats.py_stddev(values, ddof))

	def testMean(self):
		# Test that the numpy and the builtin versions behave the same.
		self.__testMeanImpl([])
		self.__testMeanImpl([1])
		self.__testMeanImpl([1, 2, 4])
		self.__testMeanImpl([-1, 2, -4])
		self.__testMeanImpl([1.04, 2.07, 4.41324])

	def testStdDev(self):
		# Test that the numpy and the builtin versions behave the same.
		self.__testStdDevImpl([], 0)
		self.__testStdDevImpl([], 1)
		self.__testStdDevImpl([1], 0)
		self.__testStdDevImpl([1], 1)
		self.__testStdDevImpl([1, 2, 4], 0)
		self.__testStdDevImpl([1, 2, 4], 3)
		self.__testStdDevImpl([1, 2, 4], 4)
		self.__testStdDevImpl([-1, 2, -4], 0)
		self.__testStdDevImpl([-1, 2, -4], 3)
		self.__testStdDevImpl([-1, 2, -4], 4)

		self.__testStdDevImpl([-1.034, 2.012341, -4], 0)
		self.__testStdDevImpl([-1.034, 2.012341, -4], 3)
		self.__testStdDevImpl([-1.034, 2.012341, -4], 4)

def getTestCases():
	ret = []
	ret.append(StatsTestCase("testMean"))
	ret.append(StatsTestCase("testStdDev"))
	return ret

