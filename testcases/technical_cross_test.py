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

from pyalgotrade.technical import cross
from pyalgotrade.technical import ma
from pyalgotrade import dataseries

class TestCase(unittest.TestCase):
	def __buildCrossTechnical(self, cls, values1, values2, period):
		ds1 = dataseries.SequenceDataSeries(values1)
		ds2 = dataseries.SequenceDataSeries(values2)
		return cls(ds1, ds2, period)

	def testCrossAboveOnce(self):
		values1 = [1, 1, 1, 10, 1, 1, 1]
		values2 = [2, 2, 2,  2, 2, 2, 2]

		# Check every 2 values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 2)
		for i in range(0, 3):
			self.assertTrue(crs[i] == 0)
		self.assertTrue(crs[3] == 1)
		for i in range(4, len(values1)):
			self.assertTrue(crs[i] == 0)

		# Check datetimes.
		self.assertEqual(len(crs.getDateTimes()), len(values1))
		for i in range(len(crs)):
			self.assertEqual(crs.getDateTimes()[i], None)

		# Check every 3 values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 3)
		for i in range(0, 3):
			self.assertTrue(crs[i] == 0)
		for i in range(3, 5):
			self.assertTrue(crs[i] == 1)
		for i in range(5, len(values1)):
			self.assertTrue(crs[i] == 0)

		# Check for all values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 100)
		self.assertTrue(crs[-1] == 1)

	def testCrossAboveMany(self):
		count = 100
		values1 = [-1 if i % 2 == 0 else 1 for i in range(count)]
		values2 = [0 for i in range(count)]

		# Check every 2 values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 2)
		self.assertTrue(crs[0] == 0)
		for i in range(1, count):
			if i % 2 == 0:
				self.assertTrue(crs[i] == 0)
			else:
				self.assertTrue(crs[i] == 1)

		# Check every 4 values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 4)
		for i in range(3, count):
			if i % 2 == 0:
				self.assertTrue(crs[i] == 1)
			else:
				self.assertTrue(crs[i] == 2)

		# Check for all values.
		crs = self.__buildCrossTechnical(cross.CrossAbove, values1, values2, 100)
		self.assertTrue(crs[-1] == count / 2)

	def testCrossBelowOnce(self):
		values1 = [1, 1, 1, 10, 1, 1, 1]
		values2 = [2, 2, 2,  2, 2, 2, 2]

		# Check every 2 values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 2)
		for i in range(0, 4):
			self.assertTrue(crs[i] == 0)
		self.assertTrue(crs[4] == 1)
		for i in range(5, len(values1)):
			self.assertTrue(crs[i] == 0)

		# Check datetimes.
		self.assertEqual(len(crs.getDateTimes()), len(values2))
		for i in range(len(crs)):
			self.assertEqual(crs.getDateTimes()[i], None)

		# Check every 3 values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 3)
		for i in range(0, 4):
			self.assertTrue(crs[i] == 0)
		for i in range(4, 6):
			self.assertTrue(crs[i] == 1)

		self.assertTrue(crs[6] == 0)

		# Check for all values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 100)
		self.assertTrue(crs[-1] == 1)

	def testCrossBelowMany(self):
		count = 100
		values1 = [-1 if i % 2 == 0 else 1 for i in range(count)]
		values2 = [0 for i in range(count)]

		# Check every 2 values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 2)
		self.assertTrue(crs[1] == 0)
		for i in range(2, count):
			if i % 2 == 0:
				self.assertTrue(crs[i] == 1)
			else:
				self.assertTrue(crs[i] == 0)

		# Check every 4 values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 4)
		for i in range(3, count):
			if i % 2 == 0:
				self.assertTrue(crs[i] == 2)
			else:
				self.assertTrue(crs[i] == 1)

		# Check for all values.
		crs = self.__buildCrossTechnical(cross.CrossBelow, values1, values2, 100)
		self.assertTrue(crs[-1] == count / 2 - 1)

	def testWithSMAs(self):
		ds1 = dataseries.SequenceDataSeries()
		ds2 = dataseries.SequenceDataSeries()
		crs = cross.CrossAbove(ma.SMA(ds1, 15),  ma.SMA(ds2, 25), 2)
		for i in range(100):
			ds1.appendValue(i)
			ds2.appendValue(50)
			if i < 24:
				self.assertTrue(crs[-1] == None)
			elif i == 58:
				self.assertTrue(crs[-1] == 1)
			else:
				self.assertTrue(crs[-1] == 0)

		# Check datetimes.
		self.assertEqual(len(crs.getDateTimes()), 100)
		self.assertEqual(crs.getDateTimes(), ds1.getDateTimes())
		for i in range(len(crs)):
			self.assertEqual(crs.getDateTimes()[i], None)

def getTestCases():
	ret = []

	ret.append(TestCase("testCrossAboveOnce"))
	ret.append(TestCase("testCrossAboveMany"))
	ret.append(TestCase("testCrossBelowOnce"))
	ret.append(TestCase("testCrossBelowMany"))
	ret.append(TestCase("testWithSMAs"))
	return ret

