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
from pyalgotrade.technical import stats
from pyalgotrade import dataseries
import numpy

class TestCase(unittest.TestCase):
	def testStdDev_1(self):
		ds = dataseries.SequenceDataSeries([1, 1, 2, 3, 5])
		stdDev = stats.StdDev(ds, 1)
		for i in stdDev:
			self.assertEquals(i, 0)

	def testStdDev(self):
		ds = dataseries.SequenceDataSeries([1, 1, 2, 3, 5])
		stdDev = stats.StdDev(ds, 2)
		self.assertEquals(stdDev[0], None)
		self.assertEquals(stdDev[1], numpy.array([1, 1]).std())
		self.assertEquals(stdDev[2], numpy.array([1, 2]).std())
		self.assertEquals(stdDev[3], numpy.array([2, 3]).std())
		self.assertEquals(stdDev[4], numpy.array([3, 5]).std())

def getTestCases():
	ret = []
	ret.append(TestCase("testStdDev_1"))
	ret.append(TestCase("testStdDev"))
	return ret

