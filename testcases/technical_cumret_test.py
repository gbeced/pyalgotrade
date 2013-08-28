# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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
from pyalgotrade import dataseries
from pyalgotrade.technical import cumret


class CumRetTestCase(unittest.TestCase):
	def testCumRet(self):
		values = dataseries.SequenceDataSeries()
		rets = cumret.CumulativeReturn(values)
		for value in [1, 2, 3, 4, 4, 3, 1, 1.2]:
			values.append(value)
		self.assertEquals(rets[0], None)
		self.assertEquals(rets[1], 1)
		self.assertEquals(rets[2], 2)
		self.assertEquals(rets[3], 3)
		self.assertEquals(rets[4], 3)
		self.assertEquals(rets[5], 2)
		self.assertEquals(rets[6], 0)
		self.assertEquals(round(rets[7], 1), 0.2)

def getTestCases():
	ret = []

	ret.append(CumRetTestCase("testCumRet"))

	return ret

