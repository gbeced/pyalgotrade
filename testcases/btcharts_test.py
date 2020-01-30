# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import datetime

from . import common

from pyalgotrade.bitcoincharts import barfeed
from pyalgotrade.utils import dt


class TestCase(common.TestCase):
    def testLoadNoFilter(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"))
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEqual(len(loaded), 9999)

        self.assertEqual(loaded[0][0], dt.as_utc(datetime.datetime(2011, 9, 13, 13, 53, 36)))
        b = loaded[0][1].getBar("BTC", "USD")
        self.assertEqual(b.getDateTime(), dt.as_utc(datetime.datetime(2011, 9, 13, 13, 53, 36)))
        self.assertEqual(b.getClose(), 5.8)
        self.assertEqual(b.getPrice(), 5.8)
        self.assertEqual(b.getVolume(), 1.0)

        self.assertEqual(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        b = loaded[-1][1].getBar("BTC", "USD")
        self.assertEqual(b.getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        self.assertEqual(b.getClose(), 5.1)
        self.assertEqual(b.getPrice(), 5.1)
        self.assertEqual(b.getVolume(), 0.39215686)

    def testLoadFilterFrom(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(
            common.get_data_file_path("bitstampUSD.csv"), "BTC", "USD",
            fromDateTime=dt.as_utc(datetime.datetime(2012, 5, 29))
        )
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEqual(len(loaded), 646)

        self.assertEqual(loaded[0][0], dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        b = loaded[0][1].getBar("BTC", "USD")
        self.assertEqual(
            b.getDateTime(),
            dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52))
        )
        self.assertEqual(b.getClose(), 5.07)
        self.assertEqual(b.getPrice(), 5.07)
        self.assertEqual(b.getVolume(), 1.39081288)

        self.assertEqual(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        b = loaded[-1][1].getBar("BTC", "USD")
        self.assertEqual(
            b.getDateTime(),
            dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5))
        )
        self.assertEqual(b.getClose(), 5.1)
        self.assertEqual(b.getPrice(), 5.1)
        self.assertEqual(b.getVolume(), 0.39215686)

    def testLoadFilterFromAndTo(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(
            common.get_data_file_path("bitstampUSD.csv"),
            instrument="BTC", priceCurrency="USD",
            fromDateTime=dt.as_utc(datetime.datetime(2012, 5, 29)),
            toDateTime=datetime.datetime(2012, 5, 31)
        )
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEqual(len(loaded), 579)

        self.assertEqual(loaded[0][0], dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        b = loaded[0][1].getBar("BTC", "USD")
        self.assertEqual(
            b.getDateTime(),
            dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52))
        )
        self.assertEqual(b.getClose(), 5.07)
        self.assertEqual(b.getVolume(), 1.39081288)

        self.assertEqual(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 30, 23, 49, 21)))
        b = loaded[-1][1].getBar("BTC", "USD")
        self.assertEqual(
            b.getDateTime(),
            dt.as_utc(datetime.datetime(2012, 5, 30, 23, 49, 21))
        )
        self.assertEqual(b.getClose(), 5.14)
        self.assertEqual(b.getVolume(), 20)
