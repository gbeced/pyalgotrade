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

import datetime

from . import common

from pyalgotrade.technical import atr
from pyalgotrade import bar
from pyalgotrade.dataseries import bards


class TestCase(common.TestCase):
    def testStockChartsATR(self):
        # Test data from http://stockcharts.com/help/doku.php?id=chart_school:technical_indicators:average_true_range_a
        high = [48.70, 48.72, 48.90, 48.87, 48.82, 49.05, 49.20, 49.35, 49.92, 50.19, 50.12, 49.66, 49.88, 50.19, 50.36, 50.57, 50.65, 50.43, 49.63, 50.33, 50.29, 50.17, 49.32, 48.50, 48.32, 46.80, 47.80, 48.39, 48.66, 48.79]
        low = [47.790, 48.140, 48.390, 48.370, 48.240, 48.635, 48.940, 48.860, 49.500, 49.870, 49.200, 48.900, 49.430, 49.725, 49.260, 50.090, 50.300, 49.210, 48.980, 49.610, 49.200, 49.430, 48.080, 47.640, 41.550, 44.283, 47.310, 47.200, 47.900, 47.730]
        close = [48.160, 48.610, 48.750, 48.630, 48.740, 49.030, 49.070, 49.320, 49.910, 50.130, 49.530, 49.500, 49.750, 50.030, 50.310, 50.520, 50.410, 49.340, 49.370, 50.230, 49.238, 49.930, 48.430, 48.180, 46.570, 45.410, 47.770, 47.720, 48.620, 47.850]
        expected = [None, None, None, None, None, None, None, None, None, None, None, None, None, 0.56, 0.59, 0.59, 0.57, 0.62, 0.62, 0.64, 0.67, 0.69, 0.78, 0.78, 1.21, 1.30, 1.38, 1.37, 1.34, 1.32]

        # Build a bar dataseries using the test data.
        barDataSeries = bards.BarDataSeries()
        atrDS = atr.ATR(barDataSeries, 14)
        now = datetime.datetime(2000, 1, 1)
        for i in range(len(high)):
            b = bar.BasicBar(now + datetime.timedelta(days=i), close[i], high[i], low[i], close[i], 100, close[i], bar.Frequency.DAY)
            barDataSeries.append(b)
            self.assertEqual(common.safe_round(atrDS[-1], 2), expected[i])

    def testStockChartsATRAdjusted(self):
        # Test data from http://stockcharts.com/help/doku.php?id=chart_school:technical_indicators:average_true_range_a
        high = [48.70, 48.72, 48.90, 48.87, 48.82, 49.05, 49.20, 49.35, 49.92, 50.19, 50.12, 49.66, 49.88, 50.19, 50.36, 50.57, 50.65, 50.43, 49.63, 50.33, 50.29, 50.17, 49.32, 48.50, 48.32, 46.80, 47.80, 48.39, 48.66, 48.79]
        low = [47.790, 48.140, 48.390, 48.370, 48.240, 48.635, 48.940, 48.860, 49.500, 49.870, 49.200, 48.900, 49.430, 49.725, 49.260, 50.090, 50.300, 49.210, 48.980, 49.610, 49.200, 49.430, 48.080, 47.640, 41.550, 44.283, 47.310, 47.200, 47.900, 47.730]
        close = [48.160, 48.610, 48.750, 48.630, 48.740, 49.030, 49.070, 49.320, 49.910, 50.130, 49.530, 49.500, 49.750, 50.030, 50.310, 50.520, 50.410, 49.340, 49.370, 50.230, 49.238, 49.930, 48.430, 48.180, 46.570, 45.410, 47.770, 47.720, 48.620, 47.850]
        expected = [None, None, None, None, None, None, None, None, None, None, None, None, None, 0.555000, 0.593929, 0.585791, 0.568949, 0.615452, 0.617920, 0.642354, 0.674329, 0.692770, 0.775429, 0.781470, 1.209229, 1.302620, 1.380290, 1.366698, 1.336219, 1.316482]

        # Build a bar dataseries using the test data.
        barDataSeries = bards.BarDataSeries()
        atrDS = atr.ATR(barDataSeries, 14, True)
        now = datetime.datetime(2000, 1, 1)
        for i in range(len(high)):
            b = bar.BasicBar(now + datetime.timedelta(days=i), close[i], high[i], low[i], close[i], 100, close[i]/2, bar.Frequency.DAY)
            barDataSeries.append(b)
            if expected[i] is None:
                self.assertEqual(atrDS[-1], None)
            else:
                self.assertEqual(common.safe_round(atrDS[-1], 2), round(expected[i]/2, 2))
