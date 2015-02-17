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

import os

from testcases import common


class DocCodeTest(common.TestCase):
    def testTutorial1(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-1.py")
            self.assertTrue(common.compare_head("tutorial-1.output", res.get_output_lines(True)[:3]))
            self.assertTrue(common.compare_tail("tutorial-1.output", res.get_output_lines(True)[-3:]))
            self.assertTrue(res.exit_ok())

    def testTutorial2(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-2.py")
            self.assertTrue(common.compare_head("tutorial-2.output", res.get_output_lines(True)[:15]))
            self.assertTrue(common.compare_tail("tutorial-2.output", res.get_output_lines(True)[-3:]))
            self.assertTrue(res.exit_ok())

    def testTutorial3(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-3.py")
            self.assertTrue(common.compare_head("tutorial-3.output", res.get_output_lines(True)[:30]))
            self.assertTrue(common.compare_tail("tutorial-3.output", res.get_output_lines(True)[-3:]))
            self.assertTrue(res.exit_ok())

    def testTutorial4(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-4.py")
            self.assertTrue(common.compare_head("tutorial-4.output", res.get_output_lines(True)))
            self.assertTrue(res.exit_ok())

    def testCSVFeed(self):
        with common.CopyFiles([os.path.join("samples", "data", "quandl_gold_2.csv")], "."):
            code = """import sys
sys.path.append('samples')
import csvfeed_1
"""
            res = common.run_python_code(code)
            self.assertTrue(common.compare_head("csvfeed_1.output", res.get_output_lines()[0:10]))
            self.assertTrue(common.compare_tail("csvfeed_1.output", res.get_output_lines()[-10:-1]))
            self.assertTrue(res.exit_ok())


class CompInvTestCase(common.TestCase):
    def testCompInv_1(self):
        files = [os.path.join("samples", "data", src) for src in ["aeti-2011-yahoofinance.csv", "egan-2011-yahoofinance.csv", "simo-2011-yahoofinance.csv", "glng-2011-yahoofinance.csv"]]
        with common.CopyFiles(files, "."):
            res = common.run_sample_script("compinv-1.py")
            # Skip the first two lines that have debug messages from the
            # broker.
            self.assertTrue(common.compare_head("compinv-1.output", res.get_output_lines(True)[2:]))
            self.assertTrue(res.exit_ok())


class StratAnalyzerTestCase(common.TestCase):
    def testSampleStrategyAnalyzer(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("sample-strategy-analyzer.py")
            self.assertTrue(common.compare_head("sample-strategy-analyzer.output", res.get_output_lines(True)))
            self.assertTrue(res.exit_ok())


class TechnicalTestCase(common.TestCase):
    def testTechnical_1(self):
        res = common.run_sample_script("technical-1.py")
        self.assertTrue(common.compare_head("technical-1.output", res.get_output_lines(True)))
        self.assertTrue(res.exit_ok())


class SampleStratTestCase(common.TestCase):
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
            res = common.run_python_code(code)
            obtained = res.get_output_lines()[-2]
            expected = common.tail_file("statarb_erniechan.output", 1)[0]
            self.assertEquals(expected, obtained, "Got this lines %s instead" % (res.get_output_lines()))
            # self.assertTrue(common.compare_tail("statarb_erniechan.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

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
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("vwap_momentum.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

    def testSMACrossOver(self):
        files = []
        for year in range(2011, 2013):
            for symbol in ["aapl"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import sma_crossover_sample
sma_crossover_sample.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("sma_crossover.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

    def testRSI2(self):
        files = []
        for year in range(2009, 2013):
            for symbol in ["DIA"]:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import rsi2_sample
rsi2_sample.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("rsi2_sample.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

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
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("bbands.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

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
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("eventstudy.output", res.get_output_lines()[-2:-1]))
            self.assertTrue(res.exit_ok())

    def testQuandl(self):
        files = []
        for year in range(2006, 2013):
            for symbol in ["GORO"]:
                fileName = "WIKI-%s-%d-quandl.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))
        files.append(os.path.join("samples", "data", "quandl_gold_2.csv"))

        with common.CopyFiles(files, "."):
            code = """import sys
sys.path.append('samples')
import quandl_sample
quandl_sample.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(common.compare_head("quandl_sample.output", res.get_output_lines()[0:10]))
            self.assertTrue(common.compare_tail("quandl_sample.output", res.get_output_lines()[-10:-1]))
            self.assertTrue(res.exit_ok())

    def testMarketTiming(self):
        common.init_temp_path()
        files = []
        instruments = ["VTI", "VEU", "IEF", "VNQ", "DBC", "SPY"]
        for year in range(2007, 2013+1):
            for symbol in instruments:
                fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
                files.append(os.path.join("samples", "data", fileName))

        with common.CopyFiles(files, "data"):
            code = """import sys
sys.path.append('samples')
import market_timing
market_timing.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(common.compare_tail("market_timing.output", res.get_output_lines()[-10:-1]))
            self.assertTrue(res.exit_ok())


class BitcoinChartsTestCase(common.TestCase):
    def testExample1(self):
        with common.CopyFiles([os.path.join("testcases", "data", "bitstampUSD-2.csv")], "bitstampUSD.csv"):
            code = """import sys
sys.path.append('samples')
import bccharts_example_1
bccharts_example_1.main()
"""
            res = common.run_python_code(code)
            lines = common.get_file_lines("30min-bitstampUSD.csv")
            self.assertTrue(common.compare_head("30min-bitstampUSD-2.csv", lines[0:10], "testcases/data"))
            self.assertTrue(common.compare_tail("30min-bitstampUSD-2.csv", lines[-10:], "testcases/data"))
            os.remove("30min-bitstampUSD.csv")
            self.assertTrue(res.exit_ok())

    def testExample2(self):
        with common.CopyFiles([os.path.join("testcases", "data", "30min-bitstampUSD-2.csv")], "30min-bitstampUSD.csv"):
            code = """import sys
sys.path.append('samples')
import bccharts_example_2
bccharts_example_2.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(
                common.compare_head("bccharts_example_2.output", res.get_output_lines()[0:10], "testcases/data")
            )
            self.assertTrue(
                common.compare_tail("bccharts_example_2.output", res.get_output_lines()[-10:-1], "testcases/data")
            )
            self.assertTrue(res.exit_ok())
