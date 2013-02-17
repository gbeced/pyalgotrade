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
import common
from pyalgotrade.technical import vwap
from pyalgotrade.barfeed import yahoofeed

class VWAPTestCase(unittest.TestCase):
	Instrument = "orcl"

	def __getFeed(self):
		# Load the feed and process all bars.
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV(VWAPTestCase.Instrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
		for i in barFeed:
			pass
		return barFeed

	def testPeriod1_ClosingPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 1)
		for i in xrange(len(bars)):
			self.assertEqual(round(bars[i].getClose(), 5), round(vwap_[i], 5))

	def testPeriod1_TypicalPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 1, True)
		for i in xrange(len(bars)):
			self.assertEqual(round(bars[i].getTypicalPrice(), 5), round(vwap_[i], 5))

	def testPeriod2_ClosingPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 2)
		self.assertEqual(vwap_[0], None)
		for i in xrange(1, len(vwap_)):
			self.assertNotEqual(vwap_[i], None)

	def testPeriod2_TypicalPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 2, True)
		self.assertEqual(vwap_[0], None)
		for i in xrange(1, len(vwap_)):
			self.assertNotEqual(vwap_[i], None)

	def testPeriod50_ClosingPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 50)
		for i in xrange(49):
			self.assertEqual(vwap_[i], None)
		for i in xrange(49, len(vwap_)):
			self.assertNotEqual(vwap_[i], None)

	def testPeriod50_TypicalPrice(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		vwap_ = vwap.VWAP(bars, 50, True)
		for i in xrange(49):
			self.assertEqual(vwap_[i], None)
		for i in xrange(49, len(vwap_)):
			self.assertNotEqual(vwap_[i], None)

def getTestCases():
	ret = []

	ret.append(VWAPTestCase("testPeriod1_ClosingPrice"))
	ret.append(VWAPTestCase("testPeriod1_TypicalPrice"))
	ret.append(VWAPTestCase("testPeriod2_ClosingPrice"))
	ret.append(VWAPTestCase("testPeriod2_TypicalPrice"))
	ret.append(VWAPTestCase("testPeriod50_ClosingPrice"))
	ret.append(VWAPTestCase("testPeriod50_TypicalPrice"))


	return ret

