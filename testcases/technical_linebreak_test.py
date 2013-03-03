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
from pyalgotrade.technical import linebreak
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

	def test2LineBreak(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		lineBreak = linebreak.LineBreak(bars, 2)

		self.assertEqual(len(lineBreak), 77)
		self.assertEqual(bars[0].getLow(), lineBreak[0].getLow())
		self.assertEqual(bars[0].getHigh(), lineBreak[0].getHigh())
		self.assertEqual(bars[0].getClose() > bars[0].getOpen(), lineBreak[0].isWhite())
		self.assertEqual(lineBreak[76].getLow(), 13.81)
		self.assertEqual(lineBreak[76].getHigh(), 13.99)
		self.assertEqual(lineBreak[76].isWhite(), False)
		self.assertEqual(lineBreak[76].isBlack(), True)

	def test3LineBreak(self):
		barFeed = self.__getFeed()
		bars = barFeed[VWAPTestCase.Instrument]
		lineBreak = linebreak.LineBreak(bars, 3)

		self.assertEqual(len(lineBreak), 33)
		self.assertEqual(bars[0].getLow(), lineBreak[0].getLow())
		self.assertEqual(bars[0].getHigh(), lineBreak[0].getHigh())
		self.assertEqual(bars[0].getClose() > bars[0].getOpen(), lineBreak[0].isWhite())
		self.assertEqual(lineBreak[32].getLow(), 10.76)
		self.assertEqual(lineBreak[32].getHigh(), 10.92)
		self.assertEqual(lineBreak[32].isWhite(), False)
		self.assertEqual(lineBreak[32].isBlack(), True)

def getTestCases():
	ret = []

	ret.append(VWAPTestCase("test2LineBreak"))
	ret.append(VWAPTestCase("test3LineBreak"))

	return ret

