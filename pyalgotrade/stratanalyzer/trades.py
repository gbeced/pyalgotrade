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

class BasicAnalyzer(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that performs some basic analysis like: 
	 * Total number of trades
	 * Total number of winning trades
	 * Total number of losing trades
	 * Total number of even trades
	 * Average profit for all trades
	 * Average profit for winning trades
	 * Average profit for losing trades
	 * Profit's standard deviation for all trades
	 * Profit's standard deviation for winning trades
	 * Profit's standard deviation for losing trades

	.. note::

		A trade is a position whose entry and exit orders were filled.
	"""

	def __init__(self):
		self.__allPositions = []
		self.__winningPositions = []
		self.__losingPositions = []
		self.__evenPositions = []

	def onPositionExitOk(self, strat, position):
		netProfit = position.getProfitLoss(True)

		self.__allPositions.append(netProfit)

		if netProfit > 0:
			self.__winningPositions.append(netProfit)
		elif netProfit < 0:
			self.__losingPositions.append(netProfit)
		else:
			self.__evenPositions.append(0)

	def getEvenCount(self):
		"""Returns the number of trades whose net profit was 0."""
		return len(self.__evenPositions)

	def getCount(self):
		"""Returns the total number of trades."""
		return len(self.__allPositions)

	def getMean(self):
		"""Returns the average profit for all the trades, or None if there are no trades."""
		return stats.mean(self.__allPositions)

	def getStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for all the trades, or None if there are no trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""
		return stats.stddev(self.__allPositions, ddof)

	def getWinningCount(self):
		"""Returns the number of trades whose net profit was > 0."""
		return len(self.__winningPositions)

	def getWinningMean(self):
		"""Returns the average profit for the winning trades, or None if there are no winning trades."""
		return stats.mean(self.__winningPositions)

	def getWinningStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for the winning trades, or None if there are no winning trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""
		return stats.stddev(self.__winningPositions, ddof)

	def getLosingCount(self):
		"""Returns the number of trades whose net profit was < 0."""
		return len(self.__losingPositions)

	def getLosingMean(self):
		"""Returns the average profit for the losing trades, or None if there are no losing trades."""
		return stats.mean(self.__losingPositions)

	def getLosingStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for the losing trades, or None if there are no losing trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""

		return stats.stddev(self.__losingPositions, ddof)

