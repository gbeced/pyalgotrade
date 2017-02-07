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


def init_data_path():
    storage = "data"
    if not os.path.exists(storage):
        os.mkdir(storage)


class DocCodeTest(common.TestCase):
    def testTutorial1(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-1.py")
            self.assertEqual(
                common.head_file("tutorial-1.output", 3),
                res.get_output_lines(True)[:3]
            )
            self.assertEqual(
                common.tail_file("tutorial-1.output", 3),
                res.get_output_lines(True)[-3:]
            )
            self.assertTrue(res.exit_ok())

    def testTutorial2(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-2.py")
            self.assertEqual(
                common.head_file("tutorial-2.output", 15),
                res.get_output_lines(True)[:15]
            )
            self.assertEqual(
                common.tail_file("tutorial-2.output", 3),
                res.get_output_lines(True)[-3:]
            )
            self.assertTrue(res.exit_ok())

    def testTutorial3(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-3.py")
            self.assertEqual(
                common.head_file("tutorial-3.output", 30),
                res.get_output_lines(True)[:30]
            )
            self.assertEqual(
                common.tail_file("tutorial-3.output", 3),
                res.get_output_lines(True)[-3:]
            )
            self.assertTrue(res.exit_ok())

    def testTutorial4(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("tutorial-4.py")
            lines = res.get_output_lines(True)
            self.assertEqual(
                common.head_file("tutorial-4.output", len(lines)),
                lines
            )
            self.assertTrue(res.exit_ok())

    def testCSVFeed(self):
        with common.CopyFiles([os.path.join("samples", "data", "quandl_gold_2.csv")], "."):
            code = """import sys
sys.path.append('samples')
import csvfeed_1
"""
            res = common.run_python_code(code)
            lines = res.get_output_lines(True)
            self.assertEqual(
                common.head_file("csvfeed_1.output", 10),
                lines[0:10]
            )
            self.assertEqual(
                common.tail_file("csvfeed_1.output", 10),
                lines[-10:]
            )
            self.assertTrue(res.exit_ok())


class CompInvTestCase(common.TestCase):
    def testCompInv_1(self):
        files = [os.path.join("samples", "data", src) for src in ["aeti-2011-yahoofinance.csv", "egan-2011-yahoofinance.csv", "simo-2011-yahoofinance.csv", "glng-2011-yahoofinance.csv"]]
        with common.CopyFiles(files, "."):
            res = common.run_sample_script("compinv-1.py")

            self.assertTrue(res.exit_ok())
            # Skip the first two lines that have debug messages from the broker.
            lines = res.get_output_lines()[2:]
            self.assertEqual(
                lines,
                common.head_file("compinv-1.output", len(lines))
            )


class StratAnalyzerTestCase(common.TestCase):
    def testSampleStrategyAnalyzer(self):
        with common.CopyFiles([os.path.join("testcases", "data", "orcl-2000.csv")], "."):
            res = common.run_sample_script("sample-strategy-analyzer.py")

            self.assertTrue(res.exit_ok())
            lines = res.get_output_lines()
            self.assertEqual(
                lines,
                common.head_file("sample-strategy-analyzer.output", len(lines))
            )


class TechnicalTestCase(common.TestCase):
    def testTechnical_1(self):
        res = common.run_sample_script("technical-1.py")

        self.assertTrue(res.exit_ok())
        lines = res.get_output_lines()
        self.assertEqual(
            lines,
            common.head_file("technical-1.output", len(lines))
        )


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

            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("statarb_erniechan.output", 1)
            )

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

            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("vwap_momentum.output", 1)
            )

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

            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("sma_crossover.output", 1)
            )

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

            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("rsi2_sample.output", 1)
            )

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
            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("bbands.output", 1)
            )

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
            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-1:],
                common.tail_file("eventstudy.output", 1)
            )

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
            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[0:10],
                common.head_file("quandl_sample.output", 10)
            )
            self.assertEqual(
                res.get_output_lines()[-10:],
                common.tail_file("quandl_sample.output", 10)
            )

    def testMarketTiming(self):
        init_data_path()
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
            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[-10:],
                common.tail_file("market_timing.output", 10)
            )


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
            os.remove("30min-bitstampUSD.csv")

            self.assertTrue(res.exit_ok())
            self.assertEqual(
                lines[0:10],
                common.head_file("30min-bitstampUSD-2.csv", 10, path="testcases/data")
            )
            self.assertEqual(
                lines[-10:],
                common.tail_file("30min-bitstampUSD-2.csv", 10, path="testcases/data")
            )

    def testExample2(self):
        with common.CopyFiles([os.path.join("testcases", "data", "30min-bitstampUSD-2.csv")], "30min-bitstampUSD.csv"):
            code = """import sys
sys.path.append('samples')
import bccharts_example_2
bccharts_example_2.main(False)
"""
            res = common.run_python_code(code)
            self.assertTrue(res.exit_ok())
            self.assertEqual(
                res.get_output_lines()[0:10],
                common.head_file("bccharts_example_2.output", 10, path="testcases/data")
            )
            self.assertEqual(
                res.get_output_lines()[-10:],
                common.tail_file("bccharts_example_2.output", 10, path="testcases/data")
            )
