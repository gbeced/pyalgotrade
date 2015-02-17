# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import common

from pyalgotrade.bitcoincharts import barfeed
from pyalgotrade.utils import dt


class TestCase(common.TestCase):
    def testLoadNoFilter(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"))
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEquals(len(loaded), 9999)

        self.assertEquals(loaded[0][0], dt.as_utc(datetime.datetime(2011, 9, 13, 13, 53, 36)))
        self.assertEquals(loaded[0][1]["BTC"].getDateTime(), dt.as_utc(datetime.datetime(2011, 9, 13, 13, 53, 36)))
        self.assertEquals(loaded[0][1]["BTC"].getClose(), 5.8)
        self.assertEquals(loaded[0][1]["BTC"].getPrice(), 5.8)
        self.assertEquals(loaded[0][1]["BTC"].getVolume(), 1.0)

        self.assertEquals(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        self.assertEquals(loaded[-1][1]["BTC"].getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        self.assertEquals(loaded[-1][1]["BTC"].getClose(), 5.1)
        self.assertEquals(loaded[-1][1]["BTC"].getPrice(), 5.1)
        self.assertEquals(loaded[-1][1]["BTC"].getVolume(), 0.39215686)

    def testLoadFilterFrom(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"), "bitstampUSD", fromDateTime=dt.as_utc(datetime.datetime(2012, 5, 29)))
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEquals(len(loaded), 646)

        self.assertEquals(loaded[0][0], dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        self.assertEquals(loaded[0][1]["bitstampUSD"].getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        self.assertEquals(loaded[0][1]["bitstampUSD"].getClose(), 5.07)
        self.assertEquals(loaded[0][1]["bitstampUSD"].getPrice(), 5.07)
        self.assertEquals(loaded[0][1]["bitstampUSD"].getVolume(), 1.39081288)

        self.assertEquals(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 31, 8, 41, 18, 5)))
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getClose(), 5.1)
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getPrice(), 5.1)
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getVolume(), 0.39215686)

    def testLoadFilterFromAndTo(self):
        feed = barfeed.CSVTradeFeed()
        feed.addBarsFromCSV(common.get_data_file_path("bitstampUSD.csv"), "bitstampUSD", fromDateTime=dt.as_utc(datetime.datetime(2012, 5, 29)), toDateTime=datetime.datetime(2012, 5, 31))
        loaded = [(dateTime, bars) for dateTime, bars in feed]

        self.assertEquals(len(loaded), 579)

        self.assertEquals(loaded[0][0], dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        self.assertEquals(loaded[0][1]["bitstampUSD"].getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 29, 1, 47, 52)))
        self.assertEquals(loaded[0][1]["bitstampUSD"].getClose(), 5.07)
        self.assertEquals(loaded[0][1]["bitstampUSD"].getVolume(), 1.39081288)

        self.assertEquals(loaded[-1][0], dt.as_utc(datetime.datetime(2012, 5, 30, 23, 49, 21)))
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getDateTime(), dt.as_utc(datetime.datetime(2012, 5, 30, 23, 49, 21)))
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getClose(), 5.14)
        self.assertEquals(loaded[-1][1]["bitstampUSD"].getVolume(), 20)
