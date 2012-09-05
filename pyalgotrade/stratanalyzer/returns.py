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

class ReturnsAnalyzer(stratanalyzer.StrategyAnalyzer):
	def __init__(self):
		self.__prevAdjClose = {} # Prev. adj. close per instrument
		self.__shares = {} # Shares at the end of the period (bar).
		self.__returns = []

	def onBars(self, strat, bars):
		brk = strat.getBroker()

		count = 0
		returns = 0

		# For each of the shares that were available at the end of the previous bar, calculate the return.
		for instrument, shares in self.__shares.iteritems():
			try:
				bar = bars.getBar(instrument)
				if bar == None or shares == 0:
					continue

				currAdjClose = bar.getAdjClose()
				prevAdjClose = self.__prevAdjClose[instrument]
				if shares > 0:
					partialReturn = (currAdjClose - prevAdjClose) / float(prevAdjClose)
				elif shares < 0:
					partialReturn = (currAdjClose - prevAdjClose) / float(prevAdjClose) * -1
				else:
					assert(False)

				returns += partialReturn
				count += 1
			except KeyError:
				pass

		if count > 0:
			self.__returns.append(returns / float(count))

		# Update the shares held at the end of the bar.
		self.__shares = {}
		for instrument in brk.getActiveInstruments():
			self.__shares[instrument] = brk.getShares(instrument)

		# Update previous adjusted close values.
		for instrument in bars.getInstruments():
			self.__prevAdjClose[instrument] = bars.getBar(instrument).getAdjClose()

	def getReturns(self):
		return self.__returns

class SharpeRatio(stratanalyzer.StrategyAnalyzer):
	"""A Sharpe Ratio :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`.

	.. note::
		Calculations are performed using adjusted close values.	
	"""

	def __init__(self):
		self.__returnsAnalyzer = ReturnsAnalyzer()

	def onBars(self, strat, bars):
		self.__returnsAnalyzer.onBars(strat, bars)

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
		returns = self.__returnsAnalyzer.getReturns()
		if len(returns) != 0:
			excessReturns = [dailyRet-(riskFreeRate/float(tradingPeriods)) for dailyRet in returns]
			avgExcessReturns = stats.mean(excessReturns)
			stdDevExcessReturns = stats.stddev(excessReturns, 1)
			ret = math.sqrt(tradingPeriods) * avgExcessReturns / stdDevExcessReturns
		return ret

