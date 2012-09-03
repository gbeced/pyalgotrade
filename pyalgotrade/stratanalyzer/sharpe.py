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
from pyalgotrade.utils import stats

import math

class SharpeRatio(stratanalyzer.StrategyAnalyzer):
	"""A Sharpe Ratio :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`.

	.. note::
		Calculations are performed using adjusted close values.	
	"""

	def __init__(self):
		self.__prevAdjClose = {} # Prev. adj. close per instrument
		self.__shares = {} # Shares at the end of the period (bar).
		self.__returns = []

	def onBars(self, strat, bars):
		brk = strat.getBroker()

		# For each of the shares that were available at the end of the previous bar, calculate the return.
		for instrument, shares in self.__shares.iteritems():
			try:
				bar = bars.getBar(instrument)
				if bar == None or shares == 0:
					continue

				if shares > 0:
					prevAdjClose = self.__prevAdjClose[instrument]
					currAdjClose = bar.getAdjClose()
				elif shares < 0:
					prevAdjClose = bar.getAdjClose()
					currAdjClose = self.__prevAdjClose[instrument]
				else:
					assert(False)
				self.__returns.append((currAdjClose - prevAdjClose) / float(prevAdjClose))
			except KeyError:
				pass

		# Update the shares held at the end of the bar.
		self.__shares = {}
		for instrument in brk.getActiveInstruments():
			self.__shares[instrument] = brk.getShares(instrument)

		# Update previous adjusted close values.
		for instrument in bars.getInstruments():
			self.__prevAdjClose[instrument] = bars.getBar(instrument).getAdjClose()

	def getSharpeRatio(self, riskFreeRate, tradingPeriods):
		"""
		Returns the Sharpe ratio for the strategy execution. If there are no trades, None is returned.

		:param riskFreeRate: The risk free rate per annum.
		:type riskFreeRate: int/float.
		:param tradingPeriods: The number of trading periods per annum.
		:type tradingPeriods: int.

		.. note::
			* If using daily bars, tradingPeriods should be set to 252.
			* If using hourly bars (with 6.5 trading hours a day) then tradingPeriods should be set to 1638 (252 * 6.5).
		"""
		ret = None
		if len(self.__returns) != 0:
			excessReturns = [dailyRet-(riskFreeRate/float(tradingPeriods)) for dailyRet in self.__returns]
			avgExcessReturns = stats.mean(excessReturns)
			stdDevExcessReturns = stats.stddev(excessReturns, 1)
			ret = math.sqrt(tradingPeriods) * avgExcessReturns / stdDevExcessReturns
		return ret

