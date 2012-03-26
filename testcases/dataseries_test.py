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

from pyalgotrade import dataseries
from pyalgotrade import bar

class TestBarDataSeries(unittest.TestCase):
	def testEmpty(self):
		ds = dataseries.BarDataSeries()
		self.assertTrue(ds.getValue(-2) == None)
		self.assertTrue(ds.getValue(-1) == None)
		self.assertTrue(ds.getValue() == None)
		self.assertTrue(ds.getValue(1) == None)
		self.assertTrue(ds.getValue(2) == None)

		self.assertTrue(ds.getValueAbsolute(-1) == None)
		self.assertTrue(ds.getValueAbsolute(0) == None)
		self.assertTrue(ds.getValueAbsolute(1000) == None)

	def testAppendInvalidDatetime(self):
		ds = dataseries.BarDataSeries()
		for i in range(10):
			now = datetime.datetime.now() + datetime.timedelta(seconds=i)
			ds.appendValue( bar.Bar(now, 0, 0, 0, 0, 0, 0) )
			# Adding the same datetime twice should fail
			self.assertRaises(Exception, ds.appendValue, bar.Bar(now, 0, 0, 0, 0, 0, 0))
			# Adding a previous datetime should fail
			self.assertRaises(Exception, ds.appendValue, bar.Bar(now - datetime.timedelta(seconds=i), 0, 0, 0, 0, 0, 0))

	def testNonEmpty(self):
		ds = dataseries.BarDataSeries()
		for i in range(10):
			ds.appendValue( bar.Bar(datetime.datetime.now() + datetime.timedelta(seconds=i), 0, 0, 0, 0, 0, 0) )

		for i in range(0, 10):
			self.assertTrue(ds.getValue(i) != None)

	def __testGetValue(self, ds, itemCount, value):
		for i in range(0, itemCount):
			self.assertTrue(ds.getValue(i) == value)

	def testNestedDataSeries(self):
		ds = dataseries.BarDataSeries()
		for i in range(10):
			ds.appendValue( bar.Bar(datetime.datetime.now() + datetime.timedelta(seconds=i), 2, 4, 1, 3, 10, 3) )

		self.__testGetValue(ds.getOpenDataSeries(), 10, 2)
		self.__testGetValue(ds.getCloseDataSeries(), 10, 3)
		self.__testGetValue(ds.getHighDataSeries(), 10, 4)
		self.__testGetValue(ds.getLowDataSeries(), 10, 1)
		self.__testGetValue(ds.getVolumeDataSeries(), 10, 10)
		self.__testGetValue(ds.getAdjCloseDataSeries(), 10, 3)

def getTestCases():
	ret = []
	ret.append(TestBarDataSeries("testEmpty"))
	ret.append(TestBarDataSeries("testAppendInvalidDatetime"))
	ret.append(TestBarDataSeries("testNonEmpty"))
	ret.append(TestBarDataSeries("testNestedDataSeries"))
	return ret

