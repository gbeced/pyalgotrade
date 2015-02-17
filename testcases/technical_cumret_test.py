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

from pyalgotrade import dataseries
from pyalgotrade.technical import cumret


class CumRetTestCase(common.TestCase):
    def testCumRet(self):
        values = dataseries.SequenceDataSeries()
        rets = cumret.CumulativeReturn(values)
        for value in [1, 2, 3, 4, 4, 3, 1, 1.2]:
            values.append(value)
        self.assertEqual(rets[0], None)
        self.assertEqual(rets[1], 1)
        self.assertEqual(rets[2], 2)
        self.assertEqual(rets[3], 3)
        self.assertEqual(rets[4], 3)
        self.assertEqual(rets[5], 2)
        self.assertEqual(rets[6], 0)
        self.assertEqual(round(rets[7], 1), 0.2)
