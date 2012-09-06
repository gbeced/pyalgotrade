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

from pyalgotrade.stratanalyzer import returns
from pyalgotrade.utils import stats

import math

class SharpeRatio(returns.ReturnsAnalyzer):
	"""A Sharpe Ratio :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`.

	.. note::
		Calculations are performed using adjusted close values.	
	"""

	def __init__(self):
		returns.ReturnsAnalyzer.__init__(self)
		self.__netReturns = []

	def onReturn(self, bars, netReturn, cumulativeReturn):
		if netReturn != None:
			self.__netReturns.append(netReturn)

	def getSharpeRatio(self, riskFreeRate, tradingPeriods):
		"""
		Returns the Sharpe ratio for the strategy execution. If there are no trades, None is returned.

		:param riskFreeRate: The risk free rate per annum.
		:type riskFreeRate: int/float.
		:param tradingPeriods: The number of trading periods per annum.
		:type tradingPeriods: int/float.

		.. note::
			* If using daily bars, tradingPeriods should be set to 252.
			* If using hourly bars (with 6.5 trading hours a day) then tradingPeriods should be set to 1638 (252 * 6.5).
		"""
		ret = None
		if len(self.__netReturns) != 0:
			excessReturns = [dailyRet-(riskFreeRate/float(tradingPeriods)) for dailyRet in self.__netReturns]
			avgExcessReturns = stats.mean(excessReturns)
			stdDevExcessReturns = stats.stddev(excessReturns, 1)
			ret = math.sqrt(tradingPeriods) * avgExcessReturns / stdDevExcessReturns
		return ret

