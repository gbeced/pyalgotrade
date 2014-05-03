# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
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
import os

from pyalgotrade.feed import csvfeed
from pyalgotrade import dispatcher
from pyalgotrade import marketsession
from pyalgotrade.utils import dt
import common
import feed_test


class TestCase(unittest.TestCase):
    def testBaseFeedInterface(self):
        feed = csvfeed.Feed("Date", "%Y-%m-%d")
        feed.addValuesFromCSV(common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        feed_test.tstBaseFeedInterface(self, feed)

    def testFeedWithBars(self):
        feed = csvfeed.Feed("Date", "%Y-%m-%d")
        feed.addValuesFromCSV(common.get_data_file_path("orcl-2000-yahoofinance.csv"))

        self.assertEqual(len(feed.getKeys()), 6)
        for col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
            self.assertEqual(len(feed[col]), 0)

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed)
        disp.run()

        for col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
            self.assertEqual(len(feed[col]), 252)

        self.assertEqual(feed["Open"][-1], 30.87)
        self.assertEqual(feed["High"][-1], 31.31)
        self.assertEqual(feed["Low"][-1], 28.69)
        self.assertEqual(feed["Close"][-1], 29.06)
        self.assertEqual(feed["Volume"][-1], 31655500)
        self.assertEqual(feed["Adj Close"][-1], 28.41)

    def testFeedWithQuandl(self):
        class RowFilter(csvfeed.RowFilter):
            def includeRow(self, dateTime, values):
                return dateTime.year == 2013

        feed = csvfeed.Feed("Date", "%Y-%m-%d", maxLen=40, timezone=marketsession.USEquities.timezone)
        feed.setRowFilter(RowFilter())
        feed.setTimeDelta(datetime.timedelta(hours=23, minutes=59, seconds=59))
        feed.addValuesFromCSV(os.path.join("samples", "data", "quandl_gold_2.csv"))

        for col in ["USD", "GBP", "EUR"]:
            self.assertEqual(len(feed[col]), 0)

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed)
        disp.run()

        for col in ["USD", "GBP", "EUR"]:
            self.assertEqual(len(feed[col]), 39)

        self.assertEqual(feed["USD"][-1], 1333.0)
        self.assertEqual(feed["GBP"][-1], 831.203)
        self.assertEqual(feed["EUR"][-1], 986.75)
        self.assertFalse(dt.datetime_is_naive(feed["USD"].getDateTimes()[-1]))
        self.assertEqual(feed["USD"].getDateTimes()[-1], dt.localize(datetime.datetime(2013, 9, 29, 23, 59, 59), marketsession.USEquities.timezone))
