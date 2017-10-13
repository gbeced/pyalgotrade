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

import numpy

from . import common

from pyalgotrade.technical import stats
from pyalgotrade import dataseries


class TestCase(common.TestCase):
    def testStdDev_1(self):
        values = [1, 1, 2, 3, 5]
        seqDS = dataseries.SequenceDataSeries()
        stdDev = stats.StdDev(seqDS, 1)
        for value in values:
            seqDS.append(value)
        for i in stdDev:
            self.assertEqual(i, 0)

    def testStdDev(self):
        values = [1, 1, 2, 3, 5]
        seqDS = dataseries.SequenceDataSeries()
        stdDev = stats.StdDev(seqDS, 2)
        for value in values:
            seqDS.append(value)

        self.assertEqual(stdDev[0], None)
        self.assertEqual(stdDev[1], numpy.array([1, 1]).std())
        self.assertEqual(stdDev[2], numpy.array([1, 2]).std())
        self.assertEqual(stdDev[3], numpy.array([2, 3]).std())
        self.assertEqual(stdDev[4], numpy.array([3, 5]).std())

    def testStdDev_Bounded(self):
        values = [1, 1, 2, 3, 5]
        seqDS = dataseries.SequenceDataSeries()
        stdDev = stats.StdDev(seqDS, 2, maxLen=2)
        for value in values:
            seqDS.append(value)

        self.assertEqual(stdDev[0], numpy.array([2, 3]).std())
        self.assertEqual(stdDev[1], numpy.array([3, 5]).std())

    def testZScore(self):
        values = [1.10, 2.20, 4.00, 5.10, 6.00, 7.10, 8.20, 9.00, 10.10, 3.00, 4.10, 5.20, 7.00, 8.10, 9.20, 16.00, 17.10, 18.20, 19.30, 20.40]
        expected = [None, None, None, None, 1.283041407, 1.317884611, 1.440611043, 1.355748299, 1.4123457, -1.831763202, -0.990484842, -0.388358578, 0.449889908, 1.408195169, 1.332948099, 1.867732104, 1.334258333, 1.063608066, 0.939656572, 1.414213562]
        seqDS = dataseries.SequenceDataSeries()
        zscore = stats.ZScore(seqDS, 5)
        i = 0
        for value in values:
            seqDS.append(value)
            if i >= 4:
                self.assertEqual(round(zscore[-1], 4), round(expected[i], 4))
            i += 1
