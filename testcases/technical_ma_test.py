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

import common

from pyalgotrade.technical import ma
from pyalgotrade import dataseries
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade import bar


def safe_round(number, ndigits):
    ret = None
    if number is not None:
        ret = round(number, ndigits)
    return ret


class SMATestCase(common.TestCase):
    def __buildSMA(self, period, values, smaMaxLen=None):
        seqDs = dataseries.SequenceDataSeries()
        ret = ma.SMA(seqDs, period, smaMaxLen)
        for value in values:
            seqDs.append(value)
        return ret

    def testPeriod1(self):
        sma = self.__buildSMA(1, [10, 20])

        self.assertTrue(sma[0] == 10)
        self.assertTrue(sma[1] == 20)
        self.assertTrue(sma[-1] == 20)
        self.assertTrue(sma[-2] == 10)
        with self.assertRaises(IndexError):
            sma[2]

        with self.assertRaises(IndexError):
            sma[-3]

        self.assertEqual(len(sma.getDateTimes()), 2)
        for i in range(len(sma)):
            self.assertEqual(sma.getDateTimes()[i], None)

    def testPeriod2(self):
        sma = self.__buildSMA(2, [0, 1, 2])
        self.assertEqual(sma[0], None)
        self.assertEqual(sma[1], (0+1) / float(2))
        self.assertEqual(sma[2], (1+2) / float(2))
        with self.assertRaises(IndexError):
            sma[3]

        self.assertEqual(len(sma.getDateTimes()), 3)
        for i in range(len(sma)):
            self.assertEqual(sma.getDateTimes()[i], None)

    def testPeriod2_BoundedFilter(self):
        sma = self.__buildSMA(2, [0, 1, 2, 3, 4], 2)
        self.assertEqual(sma[0], (2+3) / float(2))
        self.assertEqual(sma[1], (3+4) / float(2))
        self.assertEqual(sma[1], sma[-1])
        self.assertEqual(len(sma.getDateTimes()), 2)

    def testMultipleValues(self):
        period = 5
        values = range(1, 10)
        sma = self.__buildSMA(period, values)
        for i in xrange(period-1, len(values)):
            expected = sum(values[i-(period-1):i+1]) / float(period)
            self.assertTrue(sma[i] == expected)

    def testMultipleValuesSkippingOne(self):
        # Test SMA invalidating fast sma calculation.
        period = 5
        values = range(1, 10)
        sma = self.__buildSMA(period, values)
        for i in xrange(period-1, len(values), 2):
            expected = sum(values[i-(period-1):i+1]) / float(period)
            self.assertTrue(sma[i] == expected)

    def testStockChartsSMA(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
        common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10))

    def testNinjaTraderSMA(self):
        common.test_from_csv(self, "nt-sma-15.csv", lambda inputDS: ma.SMA(inputDS, 15), 3)

    def testSeqLikeOps(self):
        # ds and seq should be the same.
        seq = [1.0 for i in xrange(10)]
        ds = self.__buildSMA(1, seq)

        # Test length and every item.
        self.assertEqual(len(ds), len(seq))
        for i in xrange(len(seq)):
            self.assertEqual(ds[i], seq[i])

        # Test negative indices
        self.assertEqual(ds[-1], seq[-1])
        self.assertEqual(ds[-2], seq[-2])
        self.assertEqual(ds[-9], seq[-9])

        # Test slices
        sl = slice(0, 1, 2)
        self.assertEqual(ds[sl], seq[sl])
        sl = slice(0, 9, 2)
        self.assertEqual(ds[sl], seq[sl])
        sl = slice(0, -1, 1)
        self.assertEqual(ds[sl], seq[sl])

        for i in xrange(-100, 100):
            self.assertEqual(ds[i:], seq[i:])

        for step in xrange(1, 10):
            for i in xrange(-100, 100):
                self.assertEqual(ds[i::step], seq[i::step])

    def testEventWindow(self):
        ds = dataseries.SequenceDataSeries()
        smaEW = ma.SMAEventWindow(10)
        sma = ma.SMA(ds, 10)
        smaEW.onNewValue(None, None)  # This value should get skipped
        for i in xrange(100):
            ds.append(i)
            smaEW.onNewValue(None, i)
            self.assertEqual(sma[-1], smaEW.getValue())
            smaEW.onNewValue(None, None)  # This value should get skipped

    def testStockChartsSMA_BoundedSeq(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
        common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10), maxLen=1)
        common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10), maxLen=2)
        common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10), maxLen=4)
        common.test_from_csv(self, "sc-sma-10.csv", lambda inputDS: ma.SMA(inputDS, 10), maxLen=1000)


class WMATestCase(common.TestCase):
    def __buildWMA(self, weights, values, seqMaxLen=None, wmaMaxLen=None):
        seqDS = dataseries.SequenceDataSeries(maxLen=seqMaxLen)
        ret = ma.WMA(seqDS, weights, wmaMaxLen)
        for value in values:
            seqDS.append(value)
        return ret

    def testPeriod1(self):
        wma = self.__buildWMA([2], [10, 20])
        self.assertTrue(wma[0] == 10)
        self.assertTrue(wma[1] == 20)

        self.assertEqual(len(wma.getDateTimes()), 2)
        for i in range(len(wma)):
            self.assertEqual(wma.getDateTimes()[i], None)

    def __testPeriod2Impl(self, maxLen):
        weights = [3, 2, 1]
        values = [1, 2, 3]

        wma = self.__buildWMA(weights, values, maxLen)
        self.assertEqual(wma[0], None)
        self.assertEqual(wma[1], None)
        self.assertEqual(wma[2], (1*3 + 2*2 + 3*1) / float(3+2+1))

        self.assertEqual(len(wma.getDateTimes()), 3)
        for i in range(len(wma)):
            self.assertEqual(wma.getDateTimes()[i], None)

    def testPeriod2_BoundedSeq(self):
        self.__testPeriod2Impl(1)
        self.__testPeriod2Impl(2)
        self.__testPeriod2Impl(100)

    def testPeriod2_BoundedFilter(self):
        weights = [3, 2, 1]
        values = [1, 2, 3]

        wma = self.__buildWMA(weights, values, wmaMaxLen=2)
        self.assertEqual(wma[0], None)
        self.assertEqual(wma[1], (1*3 + 2*2 + 3*1) / float(3+2+1))
        self.assertEqual(len(wma), 2)
        self.assertEqual(len(wma[:]), 2)
        self.assertEqual(len(wma.getDateTimes()), 2)


class EMATestCase(common.TestCase):
    def testStockChartsEMA(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:moving_averages
        common.test_from_csv(self, "sc-ema-10.csv", lambda inputDS: ma.EMA(inputDS, 10), 3)

    def testMaxRecursion(self):
        barFeed = ninjatraderfeed.Feed(bar.Frequency.MINUTE)
        barFeed.addBarsFromCSV("any", common.get_data_file_path("nt-spy-minute-2011.csv"))
        ema = ma.EMA(barFeed["any"].getPriceDataSeries(), 10)
        # Load all the feed.
        barFeed.loadAll()

        # Check that the max recursion limit bug is not hit when generating the last value first.
        self.assertEqual(round(ema[-1], 2), 128.81)

    def testBoundedFilter(self):
        values = [22.2734, 22.1940, 22.0847, 22.1741, 22.1840, 22.1344, 22.2337, 22.4323, 22.2436, 22.2933, 22.1542, 22.3926, 22.3816, 22.6109, 23.3558, 24.0519, 23.7530, 23.8324, 23.9516, 23.6338, 23.8225, 23.8722, 23.6537, 23.1870, 23.0976, 23.3260, 22.6805, 23.0976, 22.4025, 22.1725]

        seqDS = dataseries.SequenceDataSeries()
        ema = ma.EMA(seqDS, 10, 2)
        for value in values:
            seqDS.append(value)

        self.assertEqual(round(ema[0], 5), 23.08068)
        self.assertEqual(round(ema[1], 5), 22.91556)
        self.assertEqual(len(ema), 2)
        self.assertEqual(len(ema[:]), 2)
        self.assertEqual(len(ema.getDateTimes()), 2)
