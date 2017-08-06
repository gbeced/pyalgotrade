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

from pyalgotrade.technical import linreg
from pyalgotrade import dataseries


class SlopeTest(common.TestCase):
    def __buildSlope(self, values, period, slopeMaxLen=None):
        seqDS = dataseries.SequenceDataSeries()
        ret = linreg.Slope(seqDS, period, slopeMaxLen)
        for value in values:
            seqDS.append(value)
        return ret

    def testSlope(self):
        slope = self.__buildSlope([1, 2, 3, 2, 1], 3)
        self.assertEqual(slope[0], None)
        self.assertEqual(slope[1], None)
        self.assertEqual(round(slope[2], 2), 1.0)
        self.assertEqual(slope[3], 0.0)
        self.assertEqual(slope[4], -1.0)

    def testSlopeBounded(self):
        slope = self.__buildSlope([1, 2, 3, 2, 1], 3, 2)
        self.assertEqual(slope[0], 0.0)
        self.assertEqual(slope[1], -1.0)


class TrendTest(common.TestCase):
    def __buildTrend(self, values, trendDays, positiveThreshold, negativeThreshold, trendMaxLen=None):
        seqDS = dataseries.SequenceDataSeries()
        ret = linreg.Trend(seqDS, trendDays, positiveThreshold, negativeThreshold, trendMaxLen)
        for value in values:
            seqDS.append(value)
        return ret

    def testTrend(self):
        trend = self.__buildTrend([1, 2, 3, 2, 1], 3, 0, 0)
        self.assertEqual(trend[0], None)
        self.assertEqual(trend[1], None)
        self.assertEqual(trend[2], True)
        self.assertEqual(trend[3], None)
        self.assertEqual(trend[4], False)

        self.assertEqual(len(trend.getDateTimes()), 5)
        for i in range(len(trend)):
            self.assertEqual(trend.getDateTimes()[i], None)

    def testTrendWithCustomThresholds(self):
        trend = self.__buildTrend([1, 2, 3, 5, -10], 3, 1, -1)
        self.assertEqual(trend[0], None)
        self.assertEqual(trend[1], None)
        self.assertEqual(trend[2], None)
        self.assertEqual(trend[3], True)
        self.assertEqual(trend[4], False)

        self.assertEqual(len(trend.getDateTimes()), 5)
        for i in range(len(trend)):
            self.assertEqual(trend.getDateTimes()[i], None)

    def testTrendWithCustomThresholds_Bounded(self):
        trend = self.__buildTrend([1, 2, 3, 5, -10], 3, 1, -1, 2)
        self.assertEqual(trend[0], True)
        self.assertEqual(trend[1], False)
        self.assertEqual(len(trend), 2)

    def testInvalidThreshold(self):
        seqDS = dataseries.SequenceDataSeries()
        with self.assertRaisesRegex(Exception, "Invalid thresholds"):
            linreg.Trend(seqDS, 10, 0.2, 0.5, 5)
