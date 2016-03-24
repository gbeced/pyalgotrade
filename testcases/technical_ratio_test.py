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

from pyalgotrade.technical import ratio
from pyalgotrade import dataseries


class TestCase(common.TestCase):
    def __buildRatio(self, values, ratioMaxLen=None):
        seqDS = dataseries.SequenceDataSeries()
        ret = ratio.Ratio(seqDS, ratioMaxLen)
        for value in values:
            seqDS.append(value)
        return ret

    def testSimple(self):
        ratio = self.__buildRatio([1, 2, 1])
        self.assertEqual(ratio[0], None)
        self.assertEqual(ratio[1], 1)
        self.assertEqual(ratio[2], -0.5)
        self.assertEqual(ratio[-1], -0.5)
        with self.assertRaises(IndexError):
            ratio[3]

        self.assertEqual(ratio[-2], ratio[1])
        self.assertEqual(ratio[-1], ratio[2])

        self.assertEqual(len(ratio.getDateTimes()), 3)
        for i in range(len(ratio)):
            self.assertEqual(ratio.getDateTimes()[i], None)

    def testNegativeValues(self):
        ratio = self.__buildRatio([-1, -2, -1])
        self.assertEqual(ratio[0], None)
        self.assertEqual(ratio[1], -1)
        self.assertEqual(ratio[2], 0.5)
        self.assertEqual(ratio[-1], 0.5)
        with self.assertRaises(IndexError):
            ratio[3]

        self.assertEqual(ratio[-2], ratio[1])
        self.assertEqual(ratio[-1], ratio[2])

        self.assertEqual(len(ratio.getDateTimes()), 3)
        for i in range(len(ratio)):
            self.assertEqual(ratio.getDateTimes()[i], None)

    def testBounded(self):
        ratio = self.__buildRatio([-1, -2, -1], 2)
        self.assertEqual(ratio[0], -1)
        self.assertEqual(ratio[1], 0.5)
        self.assertEqual(len(ratio), 2)
