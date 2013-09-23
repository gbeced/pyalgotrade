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

import os
import unittest

from pyalgotrade.tools import yahoofinance
from pyalgotrade.barfeed import yahoofeed
import common

class ToolsTestCase(unittest.TestCase):
	def testDownloadAndParse(self):
		instrument = "orcl"

		common.init_temp_path()
		path = os.path.join(common.get_temp_path(), "orcl-2010.csv")
		yahoofinance.download_daily_bars(instrument, 2010, path)
		bf = yahoofeed.Feed()
		bf.addBarsFromCSV(instrument, path)
		bf.loadAll()
		self.assertEqual(bf[instrument][-1].getOpen(), 31.22)
		self.assertEqual(bf[instrument][-1].getClose(), 31.30)

def getTestCases():
	ret = []

	ret.append(ToolsTestCase("testDownloadAndParse"))

	return ret

