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

from pyalgotrade.technical import rsi
from pyalgotrade import dataseries


class TestCase(common.TestCase):
    def testAvgGainLoss(self):
        # We divide by 2 because N samples yield N-1 averages.

        # Gain only
        avgGain, avgLoss = rsi.avg_gain_loss([1, 2, 3], 0, 3)
        self.assertTrue(avgGain == 2 / float(2))
        self.assertTrue(avgLoss == 0)

        # Loss only
        avgGain, avgLoss = rsi.avg_gain_loss([3, 2, 1], 0, 3)
        self.assertTrue(avgGain == 0)
        self.assertTrue(avgLoss == 2 / float(2))

        # Gain and Loss equal
        avgGain, avgLoss = rsi.avg_gain_loss([1, 0, 1], 0, 3)
        self.assertTrue(avgGain == 1 / float(2))
        self.assertTrue(avgLoss == 1 / float(2))

        # Gain and Loss different
        avgGain, avgLoss = rsi.avg_gain_loss([1, 3, 2], 0, 3)
        self.assertTrue(avgGain == 2 / float(2))
        self.assertTrue(avgLoss == 1 / float(2))

        # Error
        self.assertEqual(rsi.avg_gain_loss([1, 1.5, 2], 0, 1), None)
        self.assertEqual(rsi.avg_gain_loss([1, 1.5, 2], 1, 2), None)
        with self.assertRaises(IndexError):
            rsi.avg_gain_loss([1, 1.5, 2], 2, 4)

    def __buildRSI(self, values, period, rsiMaxLen=None):
        seqDS = dataseries.SequenceDataSeries()
        ret = rsi.RSI(seqDS, period, rsiMaxLen)
        for value in values:
            seqDS.append(value)
        return ret

    def testStockChartsRSI(self):
        # Test data from http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_in
        common.test_from_csv(self, "rsi-test.csv", lambda inputDS: rsi.RSI(inputDS, 14), 3)

    def testDateTimes(self):
        rsi = self.__buildRSI(range(10), 3)

        self.assertEqual(len(rsi.getDateTimes()), 10)
        for i in range(len(rsi)):
            self.assertEqual(rsi.getDateTimes()[i], None)

    def testRSIFunc(self):
        values = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433, 46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820]
        self.assertEqual(round(rsi.rsi(values, 14), 8), 70.53278948)
        values = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433, 46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820, 46.0028, 46.0328, 46.4116, 46.2222, 45.6439, 46.2122, 46.2521, 45.7137, 46.4515, 45.7835, 45.3548, 44.0288, 44.1783, 44.2181, 44.5672, 43.4205, 42.6628, 43.1314]
        self.assertEqual(round(rsi.rsi(values, 14), 8), 37.77295211)

    def testRSI_Bounded(self):
        values = [44.3389, 44.0902, 44.1497, 43.6124, 44.3278, 44.8264, 45.0955, 45.4245, 45.8433, 46.0826, 45.8931, 46.0328, 45.6140, 46.2820, 46.2820]
        rsi = self.__buildRSI(values, 14, 1)
        self.assertEqual(round(rsi[0], 8), 70.53278948)
        self.assertEqual(len(rsi), 1)
        self.assertEqual(len(rsi[:]), 1)
        self.assertEqual(len(rsi.getDateTimes()), 1)
        self.assertEqual(round(rsi[-1], 8), 70.53278948)
