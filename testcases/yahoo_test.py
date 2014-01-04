# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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
from pyalgotrade import barfeed
from pyalgotrade.barfeed import yahoofeed
import common


class ToolsTestCase(unittest.TestCase):
    def testDownloadAndParseDaily(self):
        instrument = "orcl"

        common.init_temp_path()
        path = os.path.join(common.get_temp_path(), "orcl-2010.csv")
        yahoofinance.download_daily_bars(instrument, 2010, path)
        bf = yahoofeed.Feed()
        bf.addBarsFromCSV(instrument, path)
        bf.loadAll()
        self.assertEqual(bf[instrument][-1].getOpen(), 31.22)
        self.assertEqual(bf[instrument][-1].getClose(), 31.30)

    def testDownloadAndParseWeekly(self):
        instrument = "aapl"

        common.init_temp_path()
        path = os.path.join(common.get_temp_path(), "aapl-weekly-2013.csv")
        yahoofinance.download_weekly_bars(instrument, 2013, path)
        bf = yahoofeed.Feed(frequency=barfeed.Frequency.WEEK)
        bf.addBarsFromCSV(instrument, path)
        bf.loadAll()
        self.assertEqual(bf[instrument][-1].getOpen(), 557.46)
        self.assertEqual(bf[instrument][-1].getHigh(), 561.28)
        self.assertEqual(bf[instrument][-1].getLow(), 540.43)
        self.assertEqual(bf[instrument][-1].getClose(), 540.98)
        self.assertEqual(bf[instrument][-1].getVolume(), 9852500)
