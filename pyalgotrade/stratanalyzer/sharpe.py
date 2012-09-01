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
	""" """

	def __init__(self):
		self.__prevAdjClose = {} # Prev. adj. close per instrument
		self.__dailyRet = []
		self.__activePositions = []

	def onBars(self, strat, bars):
		positionsToRemove = []

		for position in self.__activePositions:
			try:
				if position.isLong():
					prevAdjClose = self.__prevAdjClose[position.getInstrument()]
					currAdjClose = bars.getBar(position.getInstrument()).getAdjClose()
				else:
					currAdjClose = self.__prevAdjClose[position.getInstrument()]
					prevAdjClose = bars.getBar(position.getInstrument()).getAdjClose()
				self.__dailyRet.append((currAdjClose - prevAdjClose) / float(prevAdjClose))

				# We remove active positions here instead of using onPositionExitOk to avoid missing the last bar.
				if position.exitFilled():
					positionsToRemove.append(position)
			except KeyError:
				pass
	
		for position in positionsToRemove:
			self.__activePositions.remove(position)

		# Update previous adjusted close values.
		for instrument in bars.getInstruments():
			self.__prevAdjClose[instrument] = bars.getBar(instrument).getAdjClose()

	def onPositionEnterOk(self, strat, position):
		self.__activePositions.append(position)

	def getSharpeRatio(self, riskFreeRate, riskPeriod):
		"""
		For a daily strategy with 4 percent risk-free rate per annum use getSharpeRatio(0.04, 252)
		"""
		ret = None
		if len(self.__dailyRet) != 0:
			excessDailyRet = [dailyRet-(riskFreeRate/float(riskPeriod)) for dailyRet in self.__dailyRet]
			ret = math.sqrt(riskPeriod) * stats.mean(excessDailyRet) / stats.stddev(excessDailyRet, 1)
		return ret

