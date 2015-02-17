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
from pyalgotrade.technical import highlow


class HighLowTestCase(common.TestCase):
    def testHighLow(self):
        values = dataseries.SequenceDataSeries()
        high = highlow.High(values, 5)
        low = highlow.Low(values, 3)
        for value in [1, 2, 3, 4, 5]:
            values.append(value)
        self.assertEqual(high[-1], 5)
        self.assertEqual(low[-1], 3)
