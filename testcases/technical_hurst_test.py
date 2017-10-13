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

import numpy as np

from . import common

from pyalgotrade.technical import hurst
from pyalgotrade import dataseries


def build_hurst(values, period, minLags, maxLags):
    ds = dataseries.SequenceDataSeries()
    ret = hurst.HurstExponent(ds, period, minLags, maxLags)
    for value in values:
        ds.append(value)
    return ret


class TestCase(common.TestCase):
    def testHurstExpFunRandomWalk(self):
        values = np.cumsum(np.random.randn(50000)) + 1000
        h = hurst.hurst_exp(np.log10(values), 2, 20)
        self.assertEqual(round(h, 1), 0.5)

    def testHurstExpFunTrending(self):
        values = np.cumsum(np.random.randn(50000)+1) + 1000
        h = hurst.hurst_exp(np.log10(values), 2, 20)
        self.assertEqual(round(h), 1)

    def testHurstExpFunMeanRev(self):
        values = (np.random.randn(50000)) + 1000
        h = hurst.hurst_exp(np.log10(values), 2, 20)
        self.assertEqual(round(h), 0)

    def testRandomWalk(self):
        num_values = 10000
        values = np.cumsum(np.random.randn(num_values)) + 1000
        hds = build_hurst(values, num_values - 10, 2, 20)
        self.assertEqual(round(hds[-1], 1), 0.5)
        self.assertEqual(round(hds[-2], 1), 0.5)

    def testTrending(self):
        num_values = 10000
        values = np.cumsum(np.random.randn(num_values) + 10) + 1000
        hds = build_hurst(values, num_values - 10, 2, 20)
        self.assertEqual(round(hds[-1], 1), 1)
        self.assertEqual(round(hds[-2], 1), 1)

    def testMeanRev(self):
        num_values = 10000
        values = np.random.randn(num_values) + 100
        hds = build_hurst(values, num_values - 10, 2, 20)
        self.assertEqual(round(hds[-1], 1), 0)
        self.assertEqual(round(hds[-2], 1), 0)
