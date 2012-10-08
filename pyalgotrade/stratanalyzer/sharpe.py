# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import stratanalyzer
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.utils import stats

import math

class SharpeRatio(stratanalyzer.StrategyAnalyzer):
	"""A Sharpe Ratio :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`."""

	def __init__(self):
		self.__netReturns = []

	def beforeAttach(self, strat):
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = returns.ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		self.__netReturns.append(returnsAnalyzerBase.getNetReturn())

	def onReturns(self, bars, netReturn, cumulativeReturn):
		self.__netReturns.append(netReturn)

	def getSharpeRatio(self, riskFreeRate, tradingPeriods):
		"""
		Returns the Sharpe ratio for the strategy execution.
		If the standard deviation of the excess returns is 0, None is returned.

		:param riskFreeRate: The risk free rate per annum.
		:type riskFreeRate: int/float.
		:param tradingPeriods: The number of trading periods per annum.
		:type tradingPeriods: int/float.

		.. note::
			* If using daily bars, tradingPeriods should be set to 252.
			* If using hourly bars (with 6.5 trading hours a day) then tradingPeriods should be set to 252 * 6.5 = 1638.
		"""
		ret = None
		excessReturns = [dailyRet-(riskFreeRate/float(tradingPeriods)) for dailyRet in self.__netReturns]
		avgExcessReturns = stats.mean(excessReturns)
		stdDevExcessReturns = stats.stddev(excessReturns, 1)
		if stdDevExcessReturns != 0:
			ret = math.sqrt(tradingPeriods) * avgExcessReturns / stdDevExcessReturns
		return ret

