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

import common

from pyalgotrade.technical import hurst
from pyalgotrade import dataseries


def build_hurst(values, period, lags):
    ds = dataseries.SequenceDataSeries()
    ret = hurst.HurstExponent(ds, period, lags)
    for value in values:
        ds.append(value)
    return ret


class TestCase(common.TestCase):
    def testHurstExpFunRandomWalk(self):
        values = np.cumsum(np.random.randn(50000)) + 1000
        h = hurst.hurst_exp(np.log10(values), 20)
        self.assertEquals(round(h, 1), 0.5)

    def testHurstExpFunTrending(self):
        values = np.cumsum(np.random.randn(50000)+1) + 1000
        h = hurst.hurst_exp(np.log10(values), 20)
        self.assertEquals(round(h), 1)

    def testHurstExpFunMeanRev(self):
        values = (np.random.randn(50000)) + 1000
        h = hurst.hurst_exp(np.log10(values), 20)
        self.assertEquals(round(h), 0)

    def testRandomWalk(self):
        values = np.cumsum(np.random.randn(1000)) + 1000
        hds = build_hurst(values, 500, 20)
        self.assertGreater(hds[-1], 0.4)
        self.assertLess(hds[-1], 0.6)

    def testTrending(self):
        values = np.cumsum(np.random.randn(1000) + 10) + 1000
        hds = build_hurst(values, 500, 20)
        self.assertGreater(hds[-1], 0.9)
        self.assertLess(hds[-1], 1.1)

    def testMeanRev(self):
        values = np.random.randn(1000) + 100
        hds = build_hurst(values, 500, 20)
        self.assertEquals(round(hds[-1]), 0)
