# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import datetime

from . import common
from . import barfeed_test
from . import feed_test

from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade import marketsession
from pyalgotrade import bar
from pyalgotrade.utils import dt


PRICE_CURRENCY = "USD"
INSTRUMENT = "spy/%s" % PRICE_CURRENCY


class NinjaTraderTestCase(common.TestCase):
    def __loadIntradayBarFeed(self, timeZone=None):
        ret = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, timeZone)
        ret.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011.csv"))
        ret.loadAll()
        return ret

    def testBaseFeedInterface(self):
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
        barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011.csv"))
        feed_test.tstBaseFeedInterface(self, barFeed)

    def testWithTimezone(self):
        timeZone = marketsession.USEquities.getTimezone()
        barFeed = self.__loadIntradayBarFeed(timeZone)
        ds = barFeed.getDataSeries(INSTRUMENT)

        for i, currentBar in enumerate(ds):
            self.assertFalse(dt.datetime_is_naive(currentBar.getDateTime()))
            self.assertEqual(ds[i].getDateTime(), ds.getDateTimes()[i])

    def testWithoutTimezone(self):
        barFeed = self.__loadIntradayBarFeed(None)
        ds = barFeed.getDataSeries(INSTRUMENT)

        for i, currentBar in enumerate(ds):
            # Datetime must be set to UTC.
            self.assertFalse(dt.datetime_is_naive(currentBar.getDateTime()))
            self.assertEqual(ds[i].getDateTime(), ds.getDateTimes()[i])

    def testWithIntegerTimezone(self):
        try:
            barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, -3)
            self.assertTrue(False, "Exception expected")
        except Exception as e:
            self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

        try:
            barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
            barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011.csv"), -5)
            self.assertTrue(False, "Exception expected")
        except Exception as e:
            self.assertTrue(str(e).find("timezone as an int parameter is not supported anymore") == 0)

    def testLocalizeAndFilter(self):
        timezone = marketsession.USEquities.getTimezone()
        # The prices come from NinjaTrader interface when set to use 'US Equities RTH' session template.
        prices = {
            dt.localize(datetime.datetime(2011, 3, 9, 9, 31), timezone): 132.35,
            dt.localize(datetime.datetime(2011, 3, 9, 16), timezone): 132.39,
            dt.localize(datetime.datetime(2011, 3, 10, 9, 31), timezone): 130.81,
            dt.localize(datetime.datetime(2011, 3, 10, 16), timezone): 129.92,
            dt.localize(datetime.datetime(2011, 3, 11, 9, 31), timezone): 129.72,
            dt.localize(datetime.datetime(2011, 3, 11, 16), timezone): 130.84,
        }
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, timezone)
        barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011-03.csv"))
        for dateTime, bars in barFeed:
            price = prices.get(bars.getDateTime(), None)
            if price is not None:
                self.assertTrue(price == bars.getBar(INSTRUMENT).getClose())

    def testBounded(self):
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE, maxLen=2)
        barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011-03.csv"))
        barFeed.loadAll()

        barDS = barFeed.getDataSeries(INSTRUMENT)
        self.assertEqual(len(barDS), 2)
        self.assertEqual(len(barDS.getDateTimes()), 2)
        self.assertEqual(len(barDS.getCloseDataSeries()), 2)
        self.assertEqual(len(barDS.getCloseDataSeries().getDateTimes()), 2)
        self.assertEqual(len(barDS.getOpenDataSeries()), 2)
        self.assertEqual(len(barDS.getHighDataSeries()), 2)
        self.assertEqual(len(barDS.getLowDataSeries()), 2)
        self.assertEqual(len(barDS.getAdjCloseDataSeries()), 2)

    def testBaseBarFeed(self):
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
        barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011.csv"))
        barfeed_test.check_base_barfeed(self, barFeed, False)

    def testInvalidFrequency(self):
        with self.assertRaisesRegexp(Exception, "Invalid frequency.*"):
            ninjatraderfeed.Feed(bar.Frequency.WEEK)

    def testReset(self):
        barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
        barFeed.addBarsFromCSV(INSTRUMENT, common.get_data_file_path("nt-spy-minute-2011.csv"))

        barFeed.loadAll()
        ds = barFeed.getDataSeries(INSTRUMENT)

        barFeed.reset()
        barFeed.loadAll()
        reloadedDs = barFeed.getDataSeries(INSTRUMENT)

        self.assertEqual(len(reloadedDs), len(ds))
        self.assertNotEqual(reloadedDs, ds)
        for i in range(len(ds)):
            self.assertEqual(ds[i].getDateTime(), reloadedDs[i].getDateTime())
            self.assertEqual(ds[i].getClose(), reloadedDs[i].getClose())
