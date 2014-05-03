# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import unittest
import os

from testcases import common


class DocCodeTest(unittest.TestCase):
    def testTutorial1(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            lines = common.run_sample_script("tutorial-1.py").split("\n")
            self.assertTrue(common.compare_head("tutorial-1.output", lines[:3]))
            self.assertTrue(common.compare_tail("tutorial-1.output", lines[-4:-1]))

    def testTutorial2(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            lines = common.run_sample_script("tutorial-2.py").split("\n")
            self.assertTrue(common.compare_head("tutorial-2.output", lines[:15]))
            self.assertTrue(common.compare_tail("tutorial-2.output", lines[-4:-1]))

    def testTutorial3(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            lines = common.run_sample_script("tutorial-3.py").split("\n")
            self.assertTrue(common.compare_head("tutorial-3.output", lines[:30]))
            self.assertTrue(common.compare_tail("tutorial-3.output", lines[-4:-1]))

    def testTutorial4(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            lines = common.run_sample_script("tutorial-4.py").split("\n")
            self.assertTrue(common.compare_head("tutorial-4.output", lines[:-1]))

    def testCSVFeed(self):
        with common.CopyFiles([os.path.join("testcases", "data", "quandl_gold_2.csv")], "."):
            code = """import sys
sys.path.append('samples')
import csvfeed_1
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_head("csvfeed_1.output", lines[0:10]))
            self.assertTrue(common.compare_tail("csvfeed_1.output", lines[-10:-1]))


class CompInvTestCase(unittest.TestCase):
    def testCompInv_1(self):
        files = [os.path.join("samples", "data", src) for src in ["aeti-2011-yahoofinance.csv", "egan-2011-yahoofinance.csv", "simo-2011-yahoofinance.csv", "glng-2011-yahoofinance.csv"]]
        with common.CopyFiles(files, "."):
            lines = common.run_sample_script("compinv-1.py").split("\n")
            self.assertTrue(common.compare_head("compinv-1.output", lines[:-1]))


class StratAnalyzerTestCase(unittest.TestCase):
    def testSampleStrategyAnalyzer(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            lines = common.run_sample_script("sample-strategy-analyzer.py").split("\n")
            self.assertTrue(common.compare_head("sample-strategy-analyzer.output", lines[:-1]))


class TechnicalTestCase(unittest.TestCase):
    def testTechnical_1(self):
        lines = common.run_sample_script("technical-1.py").split("\n")
        self.assertTrue(common.compare_head("technical-1.output", lines[:-1]))


class SampleStratTestCase(unittest.TestCase):
    def testErnieChanGldVsGdx(self):
        files = []
        for year in range(2006, 2013):
            for symbol in ["gld", "gdx"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import statarb_erniechan
statarb_erniechan.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_tail("statarb_erniechan.output", lines[-2:-1]))

    def testVWAPMomentum(self):
        files = []
        for year in range(2011, 2013):
            for symbol in ["aapl"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import vwap_momentum
vwap_momentum.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_tail("vwap_momentum.output", lines[-2:-1]))

    def testSMACrossOver(self):
        files = []
        for year in range(2011, 2013):
            for symbol in ["aapl"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import sma_crossover
sma_crossover.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_tail("sma_crossover.output", lines[-2:-1]))


    def testBBands(self):
        files = []
        for year in range(2011, 2013):
            for symbol in ["yhoo"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import bbands
bbands.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_tail("bbands.output", lines[-2:-1]))

    def testEventStudy(self):
        files = []
        for year in range(2008, 2010):
            for symbol in ["AA", "AES", "AIG"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import eventstudy
eventstudy.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_tail("eventstudy.output", lines[-2:-1]))

    def testQuandl(self):
        files = []
        for year in range(2006, 2013):
            for symbol in ["gld"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))
        files.append(os.path.join("testcases", "data", "quandl_gold_2.csv"))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import quandl_sample
quandl_sample.main(False)
"""
            lines = common.run_python_code(code).split("\n")
            self.assertTrue(common.compare_head("quandl_sample.output", lines[0:10]))
            self.assertTrue(common.compare_tail("quandl_sample.output", lines[-10:-1]))
