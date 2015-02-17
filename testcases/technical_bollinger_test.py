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

from pyalgotrade.technical import bollinger
from pyalgotrade import dataseries


class TestCase(common.TestCase):
    def testStockChartsBollinger(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:bollinger_bands
        prices = [86.1557, 89.0867, 88.7829, 90.3228, 89.0671, 91.1453, 89.4397, 89.1750, 86.9302, 87.6752, 86.9596, 89.4299, 89.3221, 88.7241, 87.4497, 87.2634, 89.4985, 87.9006, 89.1260, 90.7043, 92.9001, 92.9784, 91.8021, 92.6647, 92.6843, 92.3021, 92.7725, 92.5373, 92.9490, 93.2039, 91.0669, 89.8318, 89.7435, 90.3994, 90.7387, 88.0177, 88.0867, 88.8439, 90.7781, 90.5416, 91.3894, 90.6500]
        expectedMiddle = [88.71, 89.05, 89.24, 89.39, 89.51, 89.69, 89.75, 89.91, 90.08, 90.38, 90.66, 90.86, 90.88, 90.91, 90.99, 91.15, 91.19, 91.12, 91.17, 91.25, 91.24, 91.17, 91.05]
        expectedUpper = [91.29, 91.95, 92.61, 92.93, 93.31, 93.73, 93.90, 94.27, 94.57, 94.79, 95.04, 94.91, 94.90, 94.90, 94.86, 94.67, 94.56, 94.68, 94.58, 94.53, 94.53, 94.37, 94.15]
        expectedLower = [86.12, 86.14, 85.87, 85.85, 85.70, 85.65, 85.59, 85.56, 85.60, 85.98, 86.27, 86.82, 86.87, 86.91, 87.12, 87.63, 87.83, 87.56, 87.76, 87.97, 87.95, 87.96, 87.95]

        seqDS = dataseries.SequenceDataSeries()
        bBands = bollinger.BollingerBands(seqDS, 20, 2)
        for value in prices:
            seqDS.append(value)

        for i in xrange(19):
            self.assertEqual(bBands.getMiddleBand()[i], None)
            self.assertEqual(bBands.getUpperBand()[i], None)
            self.assertEqual(bBands.getLowerBand()[i], None)

        for i in xrange(19, len(seqDS)):
            self.assertEqual(round(bBands.getMiddleBand()[i], 2), expectedMiddle[i-19])
            self.assertEqual(round(bBands.getUpperBand()[i], 2), expectedUpper[i-19])
            self.assertEqual(round(bBands.getLowerBand()[i], 2), expectedLower[i-19])

    def testStockChartsBollinger_Bounded(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:bollinger_bands
        prices = [86.1557, 89.0867, 88.7829, 90.3228, 89.0671, 91.1453, 89.4397, 89.1750, 86.9302, 87.6752, 86.9596, 89.4299, 89.3221, 88.7241, 87.4497, 87.2634, 89.4985, 87.9006, 89.1260, 90.7043, 92.9001, 92.9784, 91.8021, 92.6647, 92.6843, 92.3021, 92.7725, 92.5373, 92.9490, 93.2039, 91.0669, 89.8318, 89.7435, 90.3994, 90.7387, 88.0177, 88.0867, 88.8439, 90.7781, 90.5416, 91.3894, 90.6500]
        expectedMiddle = [91.24, 91.17, 91.05]
        expectedUpper = [94.53, 94.37, 94.15]
        expectedLower = [87.95, 87.96, 87.95]

        seqDS = dataseries.SequenceDataSeries()
        bBands = bollinger.BollingerBands(seqDS, 20, 2, 3)
        for value in prices:
            seqDS.append(value)

        for i in xrange(3):
            self.assertEqual(round(bBands.getMiddleBand()[i], 2), expectedMiddle[i])
            self.assertEqual(round(bBands.getUpperBand()[i], 2), expectedUpper[i])
            self.assertEqual(round(bBands.getLowerBand()[i], 2), expectedLower[i])

        self.assertEqual(len(bBands.getMiddleBand()), 3)
        self.assertEqual(len(bBands.getMiddleBand()[:]), 3)
        self.assertEqual(len(bBands.getMiddleBand().getDateTimes()), 3)
        self.assertEqual(len(bBands.getUpperBand()), 3)
        self.assertEqual(len(bBands.getUpperBand()[:]), 3)
        self.assertEqual(len(bBands.getUpperBand().getDateTimes()), 3)
        self.assertEqual(len(bBands.getLowerBand()), 3)
        self.assertEqual(len(bBands.getLowerBand()[:]), 3)
        self.assertEqual(len(bBands.getLowerBand().getDateTimes()), 3)
