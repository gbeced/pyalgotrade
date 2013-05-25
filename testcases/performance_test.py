# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import barfeed
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.utils import dt
from pyalgotrade.technical import ma
from pyalgotrade.technical import stats

import os
import datetime

import sys
sys.path.append("samples")

import smacross_strategy

profFile = "performance_test.prof"
instrument = "orcl"
feed = None

def load_intraday_bars():
	global feed

	print "Loading bars from file"
	feed = ninjatraderfeed.Feed(barfeed.Frequency.MINUTE)
	# feed.setBarFilter(csvfeed.DateRangeFilter(dt.as_utc(datetime.datetime(2008, 1, 1)), dt.as_utc(datetime.datetime(2008, 12, 31))))
	feed.setBarFilter(csvfeed.DateRangeFilter(dt.as_utc(datetime.datetime(2008, 1, 1)), dt.as_utc(datetime.datetime(2008, 3, 31))))
	feed.addBarsFromCSV(instrument, "/Users/gabo/Downloads/etf-quotes/SPY.Last.txt")

def run_smacross_strategy():
	global feed

	print "Running smacross_strategy.Strategy"
	strat = smacross_strategy.Strategy(feed, instrument, 20)
	strat.run()
	print strat.getResult()

def run_sma():
	global feed

	sma = ma.SMA(feed[instrument].getCloseDataSeries(), 200)

	print "Processing all bars"
	feed.loadAll()

	print "Processing all SMA"
	for v in sma:
		pass

def run_stddev():
	global feed

	stddev = stats.StdDev(feed[instrument].getCloseDataSeries(), 50)

	print "Processing all bars"
	feed.loadAll()
	print "Processing all StdDev"
	for v in stddev:
		pass

def main():
	# Run only one of these.
	# run_smacross_strategy()
	run_sma()
	# run_stddev()

def profile(method):
	import cProfile
	cProfile.run(method, profFile)

def printprofile():
	import pstats
	p = pstats.Stats(profFile)
	p.strip_dirs()

	# p.print_callees("__checkExitOnSessionClose")

	p.sort_stats("time")
	# p.sort_stats("cumulative")
	p.print_stats(20)

if __name__ == "__main__":
	print "PID:", os.getpid()

	# load_intraday_bars()
	# profile("load_intraday_bars()")

	# main()
	# profile("main()")

	# printprofile()

