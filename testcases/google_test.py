# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade.barfeed import googlefeed


class ToolsTestCase(common.TestCase):
    def testParseFile(self):
        instrument = "orcl"

        bf = googlefeed.Feed()
        bf.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2010-googlefinance.csv"))
        bf.loadAll()
        self.assertEqual(bf[instrument][-1].getOpen(), 31.22)
        self.assertEqual(bf[instrument][-1].getClose(), 31.30)
        self.assertEqual(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))

    def testParseMalformedFile(self):
        instrument = "orcl"

        bf = googlefeed.Feed()
        bf.addBarsFromCSV(
            instrument, common.get_data_file_path("orcl-2010-googlefinance-malformed.csv"), skipMalformedBars=True
        )
        bf.loadAll()
        self.assertEqual(bf[instrument][-1].getOpen(), 31.22)
        self.assertEqual(bf[instrument][-1].getClose(), 31.30)
        self.assertEqual(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
