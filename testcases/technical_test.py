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

from . import common

from pyalgotrade import technical
from pyalgotrade import dataseries


class TestEventWindow(technical.EventWindow):
    def __init__(self):
        technical.EventWindow.__init__(self, 1, skipNone=False, dtype=object)

    def getValue(self):
        return self.getValues()[-1]


class TestFilter(technical.EventBasedFilter):
    def __init__(self, dataSeries):
        technical.EventBasedFilter.__init__(self, dataSeries, TestEventWindow())


class DataSeriesFilterTest(common.TestCase):
    def testInvalidPosNotCached(self):
        ds = dataseries.SequenceDataSeries()
        testFilter = TestFilter(ds)
        for i in range(10):
            ds.append(i)
            ds.append(None)  # Interleave Nones.

        self.assertEqual(testFilter[-1], None)
        self.assertEqual(testFilter[-2], 9)
        self.assertEqual(testFilter[-4], 8)  # We go 3 instead of 2 because we need to skip the interleaved None values.

        self.assertEqual(testFilter[18], 9)
        self.assertEqual(testFilter[19], None)
        # Absolut pos 20 should have the next value once we insert it, but right now it should be invalid.
        with self.assertRaises(IndexError):
            testFilter[20]
        ds.append(10)
        self.assertEqual(testFilter[20], 10)
