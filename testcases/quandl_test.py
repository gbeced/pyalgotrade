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

import os
import datetime
import tempfile
import shutil
import subprocess

import six

from . import common

from pyalgotrade.tools import quandl
from pyalgotrade import bar
from pyalgotrade.barfeed import quandlfeed

try:
    # This will get environment variables set.
    from . import credentials
except:
    pass


QUANDL_API_KEY = os.getenv("QUANDL_API_KEY")
assert QUANDL_API_KEY is not None, "QUANDL_API_KEY not set"


def bytes_to_str(b):
    ret = b
    if six.PY3:
        # Convert the bytes to a string.
        ret = ret.decode()
    return ret


def check_output(*args, **kwargs):
    ret = subprocess.check_output(*args, **kwargs)
    if six.PY3:
        # Convert the bytes to a string.
        ret = bytes_to_str(ret)
    return ret


class ToolsTestCase(common.TestCase):

    def testDownloadAndParseDailyUsingApiKey(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            path = os.path.join(tmpPath, "quandl-daily-orcl-2010.csv")
            quandl.download_daily_bars("WIKI", instrument, 2010, path, authToken=QUANDL_API_KEY)
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testDownloadAndParseDaily_UseAdjClose(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            path = os.path.join(tmpPath, "quandl-daily-orcl-2010.csv")
            quandl.download_daily_bars("WIKI", instrument, 2010, path, authToken=QUANDL_API_KEY)
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, path)
            # Need to setUseAdjustedValues(True) after loading the file because we
            # can't tell in advance if adjusted values are there or not.
            bf.setUseAdjustedValues(True)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), bf[instrument][-1].getAdjClose())
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testDownloadAndParseDailyNoAdjClose(self):
        with common.TmpDir() as tmpPath:
            instrument = "IWG"
            year = 2017
            path = os.path.join(tmpPath, "quandl-daily-%s-%s.csv" % (instrument, year))
            quandl.download_daily_bars("LSE", instrument, year, path, authToken=QUANDL_API_KEY)
            bf = quandlfeed.Feed()
            bf.setNoAdjClose()
            bf.setColumnName("open", "Price")
            bf.setColumnName("close", "Price")
            bf.addBarsFromCSV(instrument, path, skipMalformedBars=True)
            bf.loadAll()
            self.assertEquals(bf[instrument][0].getDateTime(), datetime.datetime(year, 1, 3))
            self.assertEquals(bf[instrument][0].getOpen(), 237.80)
            self.assertEquals(bf[instrument][0].getHigh(), 247.00)
            self.assertEquals(bf[instrument][0].getLow(), 236.30)
            self.assertEquals(bf[instrument][0].getClose(), 237.80)
            self.assertEquals(bf[instrument][0].getVolume(), 3494173)
            self.assertEquals(bf[instrument][0].getAdjClose(), None)
            self.assertEquals(bf[instrument][0].getPrice(), 237.80)

    def testDownloadAndParseWeekly(self):
        with common.TmpDir() as tmpPath:
            instrument = "AAPL"
            path = os.path.join(tmpPath, "quandl-aapl-weekly-2010.csv")
            quandl.download_weekly_bars("WIKI", instrument, 2010, path, authToken=QUANDL_API_KEY)
            bf = quandlfeed.Feed(frequency=bar.Frequency.WEEK)
            bf.addBarsFromCSV(instrument, path)
            bf.loadAll()
            # Quandl used to report 2010-1-3 as the first week of 2010.
            self.assertTrue(
                bf[instrument][0].getDateTime() in [datetime.datetime(2010, 1, 3), datetime.datetime(2010, 1, 10)]
            )
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 26))
            self.assertEquals(bf[instrument][-1].getOpen(), 325.0)
            self.assertEquals(bf[instrument][-1].getHigh(), 325.15)
            self.assertEquals(bf[instrument][-1].getLow(), 323.17)
            self.assertEquals(bf[instrument][-1].getClose(), 323.6)
            self.assertEquals(bf[instrument][-1].getVolume(), 7969900)
            self.assertEquals(bf[instrument][-1].getPrice(), 323.6)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testInvalidFrequency(self):
        with self.assertRaisesRegexp(Exception, "Invalid frequency.*"):
            quandlfeed.Feed(frequency=bar.Frequency.MINUTE)

    def testBuildFeedDaily(self):
        with common.TmpDir() as tmpPath:
            instrument = "ORCL"
            bf = quandl.build_feed("WIKI", [instrument], 2010, 2010, tmpPath, authToken=QUANDL_API_KEY)
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testBuildFeedWeekly(self):
        with common.TmpDir() as tmpPath:
            instrument = "AAPL"
            bf = quandl.build_feed(
                "WIKI", [instrument], 2010, 2010, tmpPath, bar.Frequency.WEEK,
                authToken=QUANDL_API_KEY
            )
            bf.loadAll()
            # Quandl used to report 2010-1-3 as the first week of 2010.
            self.assertTrue(
                bf[instrument][0].getDateTime() in [datetime.datetime(2010, 1, 3), datetime.datetime(2010, 1, 10)]
            )
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 26))
            self.assertEquals(bf[instrument][-1].getOpen(), 325.0)
            self.assertEquals(bf[instrument][-1].getHigh(), 325.15)
            self.assertEquals(bf[instrument][-1].getLow(), 323.17)
            self.assertEquals(bf[instrument][-1].getClose(), 323.6)
            self.assertEquals(bf[instrument][-1].getVolume(), 7969900)
            self.assertEquals(bf[instrument][-1].getPrice(), 323.6)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)

    def testInvalidInstrument(self):
        instrument = "inexistent"

        # Don't skip errors.
        with self.assertRaisesRegexp(Exception, "404 Client Error: Not Found"):
            with common.TmpDir() as tmpPath:
                quandl.build_feed(
                    instrument, [instrument], 2010, 2010, tmpPath, bar.Frequency.WEEK,
                    authToken=QUANDL_API_KEY
                )

        # Skip errors.
        with common.TmpDir() as tmpPath:
            bf = quandl.build_feed(
                instrument, [instrument], 2010, 2010, tmpPath, bar.Frequency.WEEK, skipErrors=True,
                authToken=QUANDL_API_KEY
            )
            bf.loadAll()
            self.assertNotIn(instrument, bf)

    def testMapColumnNames(self):
        column_names = {
            "open": "Price",
            "close": "Price",
        }
        with common.TmpDir() as tmpPath:
            instrument = "IWG"
            year = 2017
            bf = quandl.build_feed(
                "LSE", [instrument], year, year, tmpPath, columnNames=column_names, skipMalformedBars=True,
                authToken=QUANDL_API_KEY
            )
            bf.setNoAdjClose()
            bf.loadAll()
            self.assertEquals(bf[instrument][0].getDateTime(), datetime.datetime(year, 1, 3))
            self.assertEquals(bf[instrument][0].getOpen(), 237.80)
            self.assertEquals(bf[instrument][0].getHigh(), 247.00)
            self.assertEquals(bf[instrument][0].getLow(), 236.30)
            self.assertEquals(bf[instrument][0].getClose(), 237.80)
            self.assertEquals(bf[instrument][0].getVolume(), 3494173)
            self.assertEquals(bf[instrument][0].getAdjClose(), None)
            self.assertEquals(bf[instrument][0].getPrice(), 237.80)

    def testExtraColumns(self):
        with common.TmpDir() as tmpPath:
            columnNames = {
                "open": "Last",
                "close": "Last"
            }
            bf = quandl.build_feed(
                "BITSTAMP", ["USD"], 2014, 2014, tmpPath, columnNames=columnNames,
                authToken=QUANDL_API_KEY
            )
            bf.loadAll()

            self.assertEquals(len(bf["USD"][-1].getExtraColumns()), 3)
            self.assertEquals(bf["USD"][-1].getExtraColumns()["Bid"], 319.19)
            self.assertEquals(bf["USD"][-1].getExtraColumns()["Ask"], 319.63)

            bids = bf["USD"].getExtraDataSeries("Bid")
            self.assertEquals(bids[-1], 319.19)

    def testNoAdjClose(self):
        with common.TmpDir() as tmpPath:
            columnNames = {
                "open": "Last",
                "close": "Last",
                "adj_close": None
            }
            bf = quandl.build_feed(
                "BITSTAMP", ["USD"], 2014, 2014, tmpPath, columnNames=columnNames,
                authToken=QUANDL_API_KEY
            )
            bf.loadAll()

            self.assertFalse(bf.barsHaveAdjClose())
            self.assertEquals(bf["USD"][-1].getAdjClose(), None)

    def testBuildFeedDailyCreatingDir(self):
        tmpPath = tempfile.mkdtemp()
        shutil.rmtree(tmpPath)
        try:
            instrument = "ORCL"
            bf = quandl.build_feed("WIKI", [instrument], 2010, 2010, tmpPath, authToken=QUANDL_API_KEY)
            bf.loadAll()

            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
            # Not checking against a specific value since this is going to change
            # as time passes by.
            self.assertNotEquals(bf[instrument][-1].getAdjClose(), None)
        finally:
            shutil.rmtree(tmpPath)

    def testCommandLineDailyCreatingDir(self):
        tmpPath = tempfile.mkdtemp()
        shutil.rmtree(tmpPath)
        try:
            instrument = "ORCL"
            subprocess.call([
                "python", "-m", "pyalgotrade.tools.quandl",
                "--source-code=WIKI",
                "--table-code=%s" % instrument,
                "--from-year=2010",
                "--to-year=2010",
                "--storage=%s" % tmpPath,
                "--auth-token=%s" % QUANDL_API_KEY
            ])
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, os.path.join(tmpPath, "WIKI-ORCL-2010-quandl.csv"))
            bf.loadAll()
            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 31))
            self.assertEquals(bf[instrument][-1].getOpen(), 31.22)
            self.assertEquals(bf[instrument][-1].getHigh(), 31.33)
            self.assertEquals(bf[instrument][-1].getLow(), 30.93)
            self.assertEquals(bf[instrument][-1].getClose(), 31.3)
            self.assertEquals(bf[instrument][-1].getVolume(), 11716300)
            self.assertEquals(bf[instrument][-1].getPrice(), 31.3)
        finally:
            shutil.rmtree(tmpPath)

    def testCommandLineWeeklyCreatingDir(self):
        tmpPath = tempfile.mkdtemp()
        shutil.rmtree(tmpPath)
        try:
            instrument = "AAPL"
            subprocess.call([
                "python", "-m", "pyalgotrade.tools.quandl",
                "--source-code=WIKI",
                "--table-code=%s" % instrument,
                "--from-year=2010",
                "--to-year=2010",
                "--storage=%s" % tmpPath,
                "--frequency=weekly",
                "--auth-token=%s" % QUANDL_API_KEY
            ])
            bf = quandlfeed.Feed()
            bf.addBarsFromCSV(instrument, os.path.join(tmpPath, "WIKI-AAPL-2010-quandl.csv"))
            bf.loadAll()

            self.assertEquals(bf[instrument][-1].getDateTime(), datetime.datetime(2010, 12, 26))
            self.assertEquals(bf[instrument][-1].getOpen(), 325.0)
            self.assertEquals(bf[instrument][-1].getHigh(), 325.15)
            self.assertEquals(bf[instrument][-1].getLow(), 323.17)
            self.assertEquals(bf[instrument][-1].getClose(), 323.6)
            self.assertEquals(bf[instrument][-1].getVolume(), 7969900)
            self.assertEquals(bf[instrument][-1].getPrice(), 323.6)
        finally:
            shutil.rmtree(tmpPath)

    def testIgnoreErrors(self):
        with common.TmpDir() as tmpPath:
            instrument = "inexistent"
            output = check_output(
                [
                    "python", "-m", "pyalgotrade.tools.quandl",
                    "--source-code=WIKI",
                    "--table-code=%s" % instrument,
                    "--from-year=2010",
                    "--to-year=2010",
                    "--storage=%s" % tmpPath,
                    "--frequency=daily",
                    "--ignore-errors"
                ],
                stderr=subprocess.STDOUT
            )
            self.assertIn("quandl [ERROR] 404 Client Error: Not Found", output)

    def testDontIgnoreErrors(self):
        with self.assertRaises(Exception) as e:
            with common.TmpDir() as tmpPath:
                instrument = "inexistent"
                check_output(
                    [
                        "python", "-m", "pyalgotrade.tools.quandl",
                        "--source-code=WIKI",
                        "--table-code=%s" % instrument,
                        "--from-year=2010",
                        "--to-year=2010",
                        "--storage=%s" % tmpPath,
                        "--frequency=daily"
                    ],
                    stderr=subprocess.STDOUT
                )
        self.assertIn("404 Client Error: Not Found", bytes_to_str(e.exception.output))
