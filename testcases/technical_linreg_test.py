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

import common

from pyalgotrade.technical import linreg
from pyalgotrade import dataseries


class LeastSquaresRegressionTestCase(common.TestCase):
    def testLsreg1(self):
        x = [0, 1, 2]
        y = [1, 2, 3]
        a, b = linreg.lsreg(x, y)
        self.assertEqual(round(a, 2), 1.0)
        self.assertEqual(round(b, 2), 1.0)

    def testLsreg2(self):
        x = [0, 1, 2]
        y = [4, 5, 6]
        a, b = linreg.lsreg(x, y)
        self.assertEqual(round(a, 2), 1.0)
        self.assertEqual(round(b, 2), 4.0)

    def testLsreg3(self):
        x = [1, 2, 3]
        y = [1, 2, 3]
        a, b = linreg.lsreg(x, y)
        self.assertEqual(round(a, 2), 1.0)
        self.assertEqual(round(b, 2), 0)

    def testStraightLine(self):
        seqDS = dataseries.SequenceDataSeries()
        lsReg = linreg.LeastSquaresRegression(seqDS, 3)

        nextDateTime = datetime.datetime(2012, 1, 1)
        seqDS.appendWithDateTime(nextDateTime, 1)
        self.assertEqual(lsReg[-1], None)

        nextDateTime = nextDateTime + datetime.timedelta(hours=1)
        seqDS.appendWithDateTime(nextDateTime, 2)
        self.assertEqual(lsReg[-1], None)

        # Check current value.
        nextDateTime = nextDateTime + datetime.timedelta(hours=1)
        seqDS.appendWithDateTime(nextDateTime, 3)
        self.assertEqual(round(lsReg[-1], 2), 3)

        # Check future values.
        futureDateTime = nextDateTime + datetime.timedelta(hours=1)
        self.assertEqual(round(lsReg.getValueAt(futureDateTime), 2), 4)
        futureDateTime = futureDateTime + datetime.timedelta(minutes=30)
        self.assertEqual(round(lsReg.getValueAt(futureDateTime), 2), 4.5)
        futureDateTime = futureDateTime + datetime.timedelta(minutes=30)
        self.assertEqual(round(lsReg.getValueAt(futureDateTime), 2), 5)

        # Move forward in sub-second increments.
        nextDateTime = nextDateTime + datetime.timedelta(milliseconds=50)
        seqDS.appendWithDateTime(nextDateTime, 4)
        nextDateTime = nextDateTime + datetime.timedelta(milliseconds=50)
        seqDS.appendWithDateTime(nextDateTime, 5)
        self.assertEqual(round(lsReg[-1], 2), 5)
