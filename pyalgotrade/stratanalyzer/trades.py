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
import numpy

class WinningLosingTrades(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that analyzes winning and losing trades during a strategy execution.
	A trade is a position whose entry/exit orders were filled.
	"""

	def __init__(self):
		self.__totalPositions = 0
		self.__winningPositions = []
		self.__losingPositions = []

	def onPositionExitOk(self, strat, position):
		self.__totalPositions += 1
		netProfit = position.getNetProfit()
		if netProfit > 0:
			self.__winningPositions.append(netProfit)
		elif netProfit < 0:
			self.__losingPositions.append(netProfit)

	def getTotalTrades(self):
		"""Returns the total number of trades."""
		return self.__totalPositions

	def getWinningTrades(self):
		"""Returns the number of trades whose net profit was > 0."""
		return len(self.__winningPositions)

	def getLosingTrades(self):
		"""Returns the number of trades whose net profit was < 0."""
		return len(self.__losingPositions)

	def getWinningTradesMean(self):
		"""Returns the average profit for the winning trades, or None if there are no winning trades."""
		ret = None
		if len(self.__winningPositions):
			ret =  numpy.array(self.__winningPositions).mean()
		return ret

	def getWinningTradesStdDev(self):
		"""Returns the profit's standard deviantion for the winning trades, or None if there are no winning trades."""
		ret = None
		if len(self.__winningPositions):
			ret =  numpy.array(self.__winningPositions).std()
		return ret

	def getLosingTradesMean(self):
		"""Returns the average profit for the losing trades, or None if there are no losing trades."""
		ret = None
		if len(self.__losingPositions):
			ret = numpy.array(self.__losingPositions).mean()
		return ret

	def getLosingTradesStdDev(self):
		"""Returns the profit's standard deviantion for the losing trades, or None if there are no losing trades."""
		ret = None
		if len(self.__losingPositions):
			ret = numpy.array(self.__losingPositions).std()
		return ret

