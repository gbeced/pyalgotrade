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

from pyalgotrade.technical import linebreak
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import dataseries
from pyalgotrade import bar
from pyalgotrade.dataseries import bards


class LineBreakTestCase(common.TestCase):
    Instrument = "orcl"

    def __getFeed(self):
        # Load the feed and process all bars.
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(LineBreakTestCase.Instrument, common.get_data_file_path("orcl-2001-yahoofinance.csv"))
        return barFeed

    def test2LineBreak(self):
        barFeed = self.__getFeed()
        bars = barFeed[LineBreakTestCase.Instrument]
        lineBreak = linebreak.LineBreak(bars, 2)
        barFeed.loadAll()

        self.assertEqual(len(lineBreak), 77)
        self.assertEqual(bars[0].getLow(), lineBreak[0].getLow())
        self.assertEqual(bars[0].getHigh(), lineBreak[0].getHigh())
        self.assertEqual(bars[0].getClose() > bars[0].getOpen(), lineBreak[0].isWhite())
        self.assertEqual(bars[0].getDateTime(), lineBreak[0].getDateTime())

        self.assertEqual(lineBreak[76].getLow(), 13.81)
        self.assertEqual(lineBreak[76].getHigh(), 13.99)
        self.assertEqual(lineBreak[76].isWhite(), False)
        self.assertEqual(lineBreak[76].isBlack(), True)

    def test3LineBreak(self):
        barFeed = self.__getFeed()
        bars = barFeed[LineBreakTestCase.Instrument]
        lineBreak = linebreak.LineBreak(bars, 3)
        barFeed.loadAll()

        self.assertEqual(len(lineBreak), 33)
        self.assertEqual(bars[0].getLow(), lineBreak[0].getLow())
        self.assertEqual(bars[0].getHigh(), lineBreak[0].getHigh())
        self.assertEqual(bars[0].getClose() > bars[0].getOpen(), lineBreak[0].isWhite())
        self.assertEqual(lineBreak[32].getLow(), 10.76)
        self.assertEqual(lineBreak[32].getHigh(), 10.92)
        self.assertEqual(lineBreak[32].isWhite(), False)
        self.assertEqual(lineBreak[32].isBlack(), True)

    def testLineBreakBounded(self):
        barFeed = self.__getFeed()
        bars = barFeed[LineBreakTestCase.Instrument]

        # Invalid maxLen, smaller than reversalLines.
        with self.assertRaises(Exception):
            lineBreak = linebreak.LineBreak(bars, 3, maxLen=2)

        lineBreak = linebreak.LineBreak(bars, 3, maxLen=4)
        # Invalid maxLen, smaller than reversalLines.
        with self.assertRaises(Exception):
            lineBreak.setMaxLen(2)
        barFeed.loadAll()

        self.assertEqual(len(lineBreak), 4)
        self.assertEqual(len(lineBreak[:]), 4)
        self.assertEqual(len(lineBreak.getDateTimes()), 4)
        self.assertEqual(lineBreak[-1].getLow(), 10.76)
        self.assertEqual(lineBreak[-1].getHigh(), 10.92)
        self.assertEqual(lineBreak[-1].isWhite(), False)
        self.assertEqual(lineBreak[-1].isBlack(), True)

    def testInvalidDataSeries(self):
        with self.assertRaisesRegexp(Exception, "barDataSeries must be a dataseries.bards.BarDataSeries instance"):
            ds = dataseries.SequenceDataSeries()
            linebreak.LineBreak(ds, 3, maxLen=2)

    def testInvalidReversalLines(self):
        with self.assertRaisesRegexp(Exception, "reversalLines must be greater than 1"):
            barFeed = self.__getFeed()
            linebreak.LineBreak(barFeed[LineBreakTestCase.Instrument], 1, maxLen=2)

    def testInvalidMaxLen(self):
        barFeed = self.__getFeed()
        lb = linebreak.LineBreak(barFeed[LineBreakTestCase.Instrument], 3, maxLen=4)
        lb.setMaxLen(3)
        with self.assertRaisesRegexp(Exception, "maxLen can't be smaller than reversalLines"):
            lb.setMaxLen(2)

    def testWhiteBlackReversal(self):
        bds = bards.BarDataSeries()
        lb = linebreak.LineBreak(bds, 2)
        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 5), 10, 12, 9, 11, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 1)
        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 6), 9, 12, 8, 12, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 1)
        self.assertEqual(lb[-1].isWhite(), True)
        self.assertEqual(lb[-1].getDateTime(), datetime.datetime(2008, 3, 5))

        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 7), 9, 12, 5, 6, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[-1].isBlack(), True)
        self.assertEqual(lb[-1].getDateTime(), datetime.datetime(2008, 3, 7))

    def testBlackWhiteReversal(self):
        bds = bards.BarDataSeries()
        lb = linebreak.LineBreak(bds, 2)
        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 5), 10, 12, 8, 9, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 1)
        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 6), 9, 12, 9, 12, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 1)
        self.assertEqual(lb[-1].isBlack(), True)
        self.assertEqual(lb[-1].getDateTime(), datetime.datetime(2008, 3, 5))

        bds.append(bar.BasicBar(datetime.datetime(2008, 3, 7), 9, 13, 5, 13, 1, None, bar.Frequency.DAY))
        self.assertEqual(len(lb), 2)
        self.assertEqual(lb[-1].isWhite(), True)
        self.assertEqual(lb[-1].getDateTime(), datetime.datetime(2008, 3, 7))
