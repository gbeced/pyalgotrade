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
import datetime

from pyalgotrade.dataseries import boundedds

class BoundedDSUnitTest(unittest.TestCase):
	def testEmpty(self):
		ds = boundedds.BoundedDataSeries(5)
		self.assertEqual(len(ds), 0)
		self.assertEqual(ds.getLength(), 0)
		self.assertEqual(ds.getFirstValidPos(), 0)
		self.assertEqual(ds.getValueAbsolute(0), None)
		self.assertEqual(ds.getValue(), None)
		with self.assertRaises(IndexError):
			ds[0]

		self.assertEqual(len(ds.getDateTimes()), 0)

	def testNotEmpty(self):
		ds = boundedds.BoundedDataSeries(2)
		ds.append(5)
		self.assertEqual(len(ds), 1)
		self.assertEqual(ds.getLength(), 1)
		self.assertEqual(ds.getFirstValidPos(), 0)
		self.assertEqual(ds.getValueAbsolute(0), 5)
		self.assertEqual(ds.getValue(), 5)
		self.assertEqual(ds[0], 5)
		self.assertEqual(ds[-1], 5)
		self.assertEqual(ds[:], [5])
		with self.assertRaises(IndexError):
			ds[1]

		self.assertEqual(len(ds.getDateTimes()), 1)
		self.assertEqual(ds.getDateTimes()[0], None)
		self.assertEqual(ds.getDateTimes()[-1], None)

	def testFull(self):
		ds = boundedds.BoundedDataSeries(2)
		ds.append(10)
		ds.append(11)
		self.assertEqual(len(ds), 2)
		self.assertEqual(ds.getLength(), 2)
		self.assertEqual(ds.getFirstValidPos(), 0)
		self.assertEqual(ds.getValueAbsolute(0), 10)
		self.assertEqual(ds.getValueAbsolute(1), 11)
		self.assertEqual(ds.getValue(), 11)
		self.assertEqual(ds.getValue(1), 10)
		self.assertEqual(ds[0], 10)
		self.assertEqual(ds[1], 11)
		self.assertEqual(ds[-1], 11)
		self.assertEqual(ds[-2], 10)
		self.assertEqual(ds[:], [10, 11])
		with self.assertRaises(IndexError):
			ds[2]

		self.assertEqual(len(ds.getDateTimes()), 2)
		self.assertEqual(ds.getDateTimes()[0], None)
		self.assertEqual(ds.getDateTimes()[1], None)
		self.assertEqual(ds.getDateTimes()[-1], None)
		self.assertEqual(ds.getDateTimes()[-2], None)

	def testFullPlusOne(self):
		ds = boundedds.BoundedDataSeries(2)
		ds.append(9)
		ds.append(10)
		ds.append(11)
		self.assertEqual(len(ds), 2)
		self.assertEqual(ds.getLength(), 2)
		self.assertEqual(ds.getFirstValidPos(), 0)
		self.assertEqual(ds.getValueAbsolute(0), 10)
		self.assertEqual(ds.getValueAbsolute(1), 11)
		self.assertEqual(ds.getValue(), 11)
		self.assertEqual(ds.getValue(1), 10)
		self.assertEqual(ds[0], 10)
		self.assertEqual(ds[1], 11)
		self.assertEqual(ds[-1], 11)
		self.assertEqual(ds[-2], 10)
		self.assertEqual(ds[:], [10, 11])
		with self.assertRaises(IndexError):
			ds[2]

		self.assertEqual(len(ds.getDateTimes()), 2)
		self.assertEqual(ds.getDateTimes()[0], None)
		self.assertEqual(ds.getDateTimes()[1], None)
		self.assertEqual(ds.getDateTimes()[-1], None)
		self.assertEqual(ds.getDateTimes()[-2], None)

	def testNotEmptyWithDateTime(self):
		dt = datetime.datetime(2000, 1, 1)
		ds = boundedds.BoundedDataSeries(2)
		ds.appendWithDateTime(dt, 5)
		self.assertEqual(len(ds), 1)
		self.assertEqual(ds.getLength(), 1)
		self.assertEqual(ds.getFirstValidPos(), 0)
		self.assertEqual(ds.getValueAbsolute(0), 5)
		self.assertEqual(ds.getValue(), 5)
		self.assertEqual(ds[0], 5)
		self.assertEqual(ds[-1], 5)
		self.assertEqual(ds[:], [5])
		with self.assertRaises(IndexError):
			ds[1]

		self.assertEqual(len(ds.getDateTimes()), 1)
		self.assertEqual(ds.getDateTimes()[0], dt)
		self.assertEqual(ds.getDateTimes()[-1], dt)

def getTestCases():
	ret = []

	ret.append(BoundedDSUnitTest("testEmpty"))
	ret.append(BoundedDSUnitTest("testNotEmpty"))
	ret.append(BoundedDSUnitTest("testFull"))
	ret.append(BoundedDSUnitTest("testFullPlusOne"))
	ret.append(BoundedDSUnitTest("testNotEmptyWithDateTime"))

	return ret

