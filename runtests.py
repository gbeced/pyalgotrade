# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

# This is necessary when running testcases on Windows.
import os
os.environ["PYTHONPATH"]="."

from testcases import technical_test
from testcases import technical_ma_test
from testcases import technical_vwap_test
from testcases import technical_ratio_test
from testcases import technical_trend_test
from testcases import technical_rsi_test
from testcases import technical_cross_test
from testcases import technical_roc_test
from testcases import technical_stoch_test
from testcases import technical_linebreak_test
from testcases import technical_stats_test
from testcases import technical_bollinger_test
from testcases import technical_highlow_test
from testcases import technical_cumret_test
from testcases import dataseries_test
from testcases import csvbarfeed_test
from testcases import dbfeed_test
from testcases import broker_test
from testcases import strategy_test
from testcases import smacrossover_strategy_test
from testcases import multi_instrument_strategy_test
from testcases import talib_test
from testcases import observer_test
from testcases import returns_analyzer_test
from testcases import trades_analyzer_test
from testcases import sharpe_analyzer_test
from testcases import drawdown_analyzer_test
from testcases import utils_test
from testcases import doc_test
from testcases import position_test
from testcases import mtgox_test
from testcases import yahoo_test
from testcases import resample_test

def getTestCases():
	ret = []

	ret += technical_test.getTestCases()
	ret += technical_ma_test.getTestCases()
	ret += technical_vwap_test.getTestCases()
	ret += technical_linebreak_test.getTestCases()
	ret += technical_ratio_test.getTestCases()
	ret += technical_trend_test.getTestCases()
	ret += technical_rsi_test.getTestCases()
	ret += technical_cross_test.getTestCases()
	ret += technical_roc_test.getTestCases()
	ret += technical_stoch_test.getTestCases()
	ret += technical_stats_test.getTestCases()
	ret += technical_bollinger_test.getTestCases()
	ret += technical_highlow_test.getTestCases()
	ret += technical_cumret_test.getTestCases()
	ret += dataseries_test.getTestCases()
	ret += csvbarfeed_test.getTestCases()
	ret += dbfeed_test.getTestCases()
	ret += broker_test.getTestCases()
	ret += strategy_test.getTestCases()
	ret += position_test.getTestCases()
	ret += smacrossover_strategy_test.getTestCases()
	ret += multi_instrument_strategy_test.getTestCases()
	ret += talib_test.getTestCases()
	ret += observer_test.getTestCases()
	ret += returns_analyzer_test.getTestCases()
	ret += trades_analyzer_test.getTestCases()
	ret += sharpe_analyzer_test.getTestCases()
	ret += drawdown_analyzer_test.getTestCases()
	ret += utils_test.getTestCases()
	ret += doc_test.getTestCases()
	ret += mtgox_test.getTestCases()
	ret += yahoo_test.getTestCases()
	ret += resample_test.getTestCases()

	return ret

def main():
	suite = unittest.TestSuite()
	suite.addTests(getTestCases())
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)

def profile():
	import cProfile
	import pstats
	profFile = "prof"
	cProfile.run("main()", profFile)
	p = pstats.Stats(profFile)
	# p.dump_stats("runtests.profile")
	p.strip_dirs().sort_stats("time").print_stats()

if __name__ == "__main__":
	main()
	# profile()

