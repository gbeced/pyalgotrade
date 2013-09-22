# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import os
import unittest
import datetime
import logging

from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import tools
import common

tools.logger.setLevel(logging.ERROR)

class TradesFeedTestCase(unittest.TestCase):
	def testDownloadAndParse(self):
		common.init_temp_path()
		path = os.path.join(common.get_temp_path(), "trades-mgtox-usd-2013-01-01.csv")
		tools.download_trades_by_day("usd", 2013, 1, 1, path)

		bf = barfeed.CSVTradeFeed()
		bf.addBarsFromCSV(path)
		bf.loadAll()
		ds = bf["BTC"]
		self.assertTrue(len(ds) > 0)
		self.assertEqual(ds[-1].getOpen(), ds[-1].getHigh())
		self.assertEqual(ds[-1].getHigh(), ds[-1].getLow())
		self.assertEqual(ds[-1].getLow(), ds[-1].getClose())
		self.assertEqual(ds[-1].getClose(), 13.30413)
		self.assertEqual(ds[-1].getVolume(), 0.01)
		self.assertEqual(ds[-1].getTradeType(), "ask")
		self.assertEqual(ds[-1].getDateTime().date(), datetime.date(2013, 1, 1))

def getTestCases():
	ret = []

	ret.append(TradesFeedTestCase("testDownloadAndParse"))

	return ret

