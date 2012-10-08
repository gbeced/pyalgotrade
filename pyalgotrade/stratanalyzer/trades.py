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
from pyalgotrade import broker
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.utils import stats

class Trades(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that performs some basic analysis on trades: 

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
	"""

	def __init__(self):
		self.__allTrades = []
		self.__winningTrades = []
		self.__losingTrades = []
		self.__evenTrades = 0
		self.__posTrackers = {}

	def __updateTrades(self, posTracker):
		price = 0 # The price doesn't matter since the position should be closed.
		assert(posTracker.getShares() == 0)
		netProfit =  posTracker.getNetProfit(price)

		if netProfit > 0:
			self.__winningTrades.append(netProfit)
		elif netProfit < 0:
			self.__losingTrades.append(netProfit)
		else:
			self.__evenTrades += 1
		self.__allTrades.append(netProfit)

		posTracker.update(price)

	def __updatePosTracker(self, posTracker, price, commission, quantity):
		currentShares = posTracker.getShares()

		if currentShares > 0: # Current position is long
			if quantity > 0: # Increase long position
				posTracker.buy(quantity, price, commission)
			else:
				newShares = currentShares + quantity
				if newShares == 0: # Exit long.
					posTracker.sell(currentShares, price, commission)
					self.__updateTrades(posTracker)
				elif newShares > 0: # Sell some shares.
					posTracker.sell(quantity*-1, price, commission)
				else: # Exit long and enter short. Use proportional commissions.
					posTracker.sell(currentShares, price, commission / float(currentShares))
					self.__updateTrades(posTracker)
					posTracker.sell(newShares*-1, price, commission / float(newShares*-1))
		elif currentShares < 0: # Current position is short
			if quantity < 0: # Increase short position
				posTracker.sell(quantity*-1, price, commission)
			else:
				newShares = currentShares + quantity
				if newShares == 0: # Exit short.
					posTracker.buy(currentShares*-1, price, commission)
					self.__updateTrades(posTracker)
				elif newShares < 0: # Re-buy some shares.
					posTracker.buy(quantity, price, commission)
				else: # Exit short and enter long. Use proportional commissions.
					posTracker.buy(currentShares*-1, price, commission / float(currentShares*-1))
					self.__updateTrades(posTracker)
					posTracker.buy(newShares, price, commission / float(newShares))
		elif quantity > 0:
			posTracker.buy(quantity, price, commission)
		else:
			posTracker.sell(quantity*-1, price, commission)

	def __onOrderUpdate(self, broker_, order):
		# Only interested in filled orders.
		if not order.isFilled():
			return

		# Get or create the tracker for this instrument.
		try:
			posTracker = self.__posTrackers[order.getInstrument()]
		except KeyError:
			posTracker = returns.PositionTracker()
			self.__posTrackers[order.getInstrument()] = posTracker

		# Update the tracker for this order.
		price = order.getExecutionInfo().getPrice()
		commission = order.getExecutionInfo().getCommission()
		action = order.getAction()
		if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			quantity = order.getExecutionInfo().getQuantity()
		elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			quantity = order.getExecutionInfo().getQuantity() * -1
		else: # Unknown action
			assert(False)

		self.__updatePosTracker(posTracker, price, commission, quantity)

	def attached(self, strat):
		strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)

	def getEvenCount(self):
		"""Returns the number of trades whose net profit was 0."""
		return self.__evenTrades

	def getCount(self):
		"""Returns the total number of trades."""
		return len(self.__allTrades)

	def getMean(self):
		"""Returns the average profit for all the trades, or None if there are no trades."""
		return stats.mean(self.__allTrades)

	def getStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for all the trades, or None if there are no trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""
		return stats.stddev(self.__allTrades, ddof)

	def getWinningCount(self):
		"""Returns the number of trades whose net profit was > 0."""
		return len(self.__winningTrades)

	def getWinningMean(self):
		"""Returns the average profit for the winning trades, or None if there are no winning trades."""
		return stats.mean(self.__winningTrades)

	def getWinningStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for the winning trades, or None if there are no winning trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""
		return stats.stddev(self.__winningTrades, ddof)

	def getLosingCount(self):
		"""Returns the number of trades whose net profit was < 0."""
		return len(self.__losingTrades)

	def getLosingMean(self):
		"""Returns the average profit for the losing trades, or None if there are no losing trades."""
		return stats.mean(self.__losingTrades)

	def getLosingStdDev(self, ddof=1):
		"""Returns the profit's standard deviation for the losing trades, or None if there are no losing trades.

		:param ddof: Delta Degrees of Freedom. The divisor used in calculations is N - ddof, where N represents the number of elements.
		:type ddof: int.
		"""
		return stats.stddev(self.__losingTrades, ddof)

