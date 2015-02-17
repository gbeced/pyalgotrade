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

from pyalgotrade.technical import macd
from pyalgotrade import dataseries


class MACDTestCase(common.TestCase):
    def testMACD(self):
        values = [16.39, 16.4999, 16.45, 16.43, 16.52, 16.51, 16.423, 16.41, 16.47, 16.45, 16.32, 16.36, 16.34, 16.59, 16.54, 16.52, 16.44, 16.47, 16.5, 16.45, 16.28, 16.07, 16.08, 16.1, 16.1, 16.09, 16.43, 16.4899, 16.59, 16.65, 16.78, 16.86, 16.86, 16.76]
        # These expected values were generated using TA-Lib
        macdValues = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0.0067, 0.0106, 0.0028, -0.0342, -0.0937, -0.1214, -0.1276, -0.125, -0.1195, -0.0459, 0.0097, 0.0601, 0.0975, 0.139, 0.1713, 0.1816, 0.1598]
        signalValues = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0.0036, 0.0056, 0.0048, -0.0064, -0.0313, -0.057, -0.0772, -0.0909, -0.0991, -0.0839, -0.0571, -0.0236, 0.011, 0.0475, 0.0829, 0.1111, 0.125]
        histogramValues = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, 0.0031, 0.005, -0.002, -0.0279, -0.0624, -0.0643, -0.0504, -0.0342, -0.0205, 0.0379, 0.0668, 0.0838, 0.0865, 0.0914, 0.0884, 0.0705, 0.0348]
        ds = dataseries.SequenceDataSeries()

        macdDs = macd.MACD(ds, 5, 13, 6)
        for i, value in enumerate(values):
            ds.append(value)
            self.assertEqual(common.safe_round(macdDs[i], 4), macdValues[i])
            self.assertEqual(common.safe_round(macdDs.getSignal()[i], 4), signalValues[i])
            self.assertEqual(common.safe_round(macdDs.getHistogram()[i], 4), histogramValues[i])
