# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

from . import common

from pyalgotrade.technical import vwap
from pyalgotrade.barfeed import yahoofeed


class VWAPTestCase(common.TestCase):
    Instrument = "orcl"

    def __getFeed(self):
        # Load the feed and process all bars.
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(VWAPTestCase.Instrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        return barFeed

    def testPeriod1_ClosingPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 1)
        barFeed.loadAll()
        for i in range(len(bars)):
            self.assertEqual(round(bars[i].getClose(), 5), round(vwap_[i], 5))

    def testPeriod1_TypicalPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 1, True)
        barFeed.loadAll()
        for i in range(len(bars)):
            self.assertEqual(round(bars[i].getTypicalPrice(), 5), round(vwap_[i], 5))

    def testPeriod2_ClosingPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 2)
        barFeed.loadAll()
        self.assertEqual(vwap_[0], None)
        for i in range(1, len(vwap_)):
            self.assertNotEqual(vwap_[i], None)

    def testPeriod2_TypicalPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 2, True)
        barFeed.loadAll()
        self.assertEqual(vwap_[0], None)
        for i in range(1, len(vwap_)):
            self.assertNotEqual(vwap_[i], None)

    def testPeriod50_ClosingPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 50)
        barFeed.loadAll()
        for i in range(49):
            self.assertEqual(vwap_[i], None)
        for i in range(49, len(vwap_)):
            self.assertNotEqual(vwap_[i], None)

    def testPeriod50_TypicalPrice(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 50, True)
        barFeed.loadAll()
        for i in range(49):
            self.assertEqual(vwap_[i], None)
        for i in range(49, len(vwap_)):
            self.assertNotEqual(vwap_[i], None)

    def testBounded(self):
        barFeed = self.__getFeed()
        bars = barFeed[VWAPTestCase.Instrument]
        vwap_ = vwap.VWAP(bars, 50, True, 2)
        barFeed.loadAll()

        outputValues = [14.605005665747331, 14.605416923506045]
        for i in range(2):
            self.assertEqual(round(vwap_[i], 4), round(outputValues[i], 4))
