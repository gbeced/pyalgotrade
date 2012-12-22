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
from pyalgotrade import observer
from pyalgotrade import dataseries

# Helper class to calculate returns and net profit.
class PositionTracker:
	def __init__(self):
		self.__shares = 0
		self.__cash = 0
		self.__commissions = 0
		self.__cost = 0

	def __updateCost(self, quantity, price):
		cost = 0

		if self.__shares > 0: # Current position is long
			if quantity > 0: # Increase long position
				cost = quantity * price
			else:
				diff = self.__shares + quantity
				if diff < 0: # Entering a short position
					cost = abs(diff) * price
		elif self.__shares < 0: # Current position is short
			if quantity < 0: # Increase short position
				cost = abs(quantity) * price
			else:
				diff = self.__shares + quantity
				if diff > 0: # Entering a long position
					cost = diff * price
		else:
			cost = abs(quantity) * price
		self.__cost += cost

	def getShares(self):
		return self.__shares

	def getCost(self):
		return self.__cost

	def getCommissions(self):
		return self.__commissions

	def getNetProfit(self, price, includeCommissions = True):
		ret = self.__cash + self.__shares * price
		if includeCommissions:
			ret -= self.__commissions
		return ret

	def getReturn(self, price, includeCommissions = True):
		ret = 0
		netProfit = self.getNetProfit(price, includeCommissions)
		cost = self.getCost()
		if cost != 0:
			ret = netProfit / float(cost)
		return ret

	def buy(self, quantity, price, commission = 0):
		assert(quantity > 0)
		self.__updateCost(quantity, price)
		self.__cash += quantity * -1 * price
		self.__shares += quantity
		self.__commissions += commission

	def sell(self, quantity, price, commission = 0):
		assert(quantity > 0)
		self.__updateCost(quantity * -1, price)
		self.__cash += quantity * price
		self.__shares -= quantity
		self.__commissions += commission

	def update(self, price):
		self.__commissions = 0
		self.__cash = self.__shares * -1 * price
		self.__cost = abs(self.__shares) * price

class ReturnsAnalyzerBase(stratanalyzer.StrategyAnalyzer):
	def __init__(self):
		self.__netRet = 0
		self.__cumRet = 0
		self.__event = observer.Event()
		self.__lastPortfolioValue = None

	@classmethod
	def getOrCreateShared(cls, strat):
		name = cls.__name__
		# Get or create the shared ReturnsAnalyzerBase.
		ret = strat.getNamedAnalyzer(name)
		if ret == None:
			ret = ReturnsAnalyzerBase()
			strat.attachAnalyzerEx(ret, name)
		return ret

	def __portfolioValue(self, strat):
		bars = strat.getFeed().getLastBars()
		if bars != None:
			ret = strat.getBroker().getValue(bars)
		else:
			ret = strat.getBroker().getCash()
		return ret

	def attached(self, strat):
		self.__lastPortfolioValue = self.__portfolioValue(strat)

	# An event will be notified when return are calculated at each bar. The hander should receive 2 parameters:
	# 1: This analyzer's instance
	# 2: The bars
	def getEvent(self):
		return self.__event

	def getNetReturn(self):
		return self.__netRet

	def getCumulativeReturn(self):
		return self.__cumRet

	def beforeOnBars(self, strat, bars):
		# assert(strat.getFeed().getLastBars() == bars)

		currentPortfolioValue = self.__portfolioValue(strat)
		netReturn = (currentPortfolioValue - self.__lastPortfolioValue) / float(self.__lastPortfolioValue)
		self.__lastPortfolioValue = currentPortfolioValue

		self.__netRet = netReturn

		# Calculate cumulative return.
		self.__cumRet = (1 + self.__cumRet) * (1 + netReturn) - 1

		# Notify that new returns are available.
		self.__event.emit(self, bars)

class Returns(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates returns and cumulative returns."""

	def __init__(self):
		self.__netRet = 0
		self.__cumRet = 0

	def beforeAttach(self, strat):
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		self.__netRet = returnsAnalyzerBase.getNetReturn()
		self.__cumRet = returnsAnalyzerBase.getCumulativeReturn()

	def getNetReturn(self):
		"""Returns the net return for the last bar."""
		return self.__netRet

	def getCumulativeReturn(self):
		"""Returns the cumulative return up to the last bar."""
		return self.__cumRet

class ReturnsDataSeries(dataseries.SequenceDataSeries):
	"""A :class:`pyalgotrade.dataseries.DataSeries` that holds net returns for each bar.

	:param strat: The strategy to calculate returns on.
	:type strat: :class:`pyalgotrade.strategy.Strategy`
	"""

	def __init__(self, strat):
		dataseries.SequenceDataSeries.__init__(self)
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		self.appendValue(returnsAnalyzerBase.getNetReturn())

class CumulativeReturnsDataSeries(dataseries.SequenceDataSeries):
	"""A :class:`pyalgotrade.dataseries.DataSeries` that holds cumulative returns for each bar.

	:param strat: The strategy to calculate cumulative returns on.
	:type strat: :class:`pyalgotrade.strategy.Strategy`
	"""

	def __init__(self, strat):
		dataseries.SequenceDataSeries.__init__(self)
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		self.appendValue(returnsAnalyzerBase.getCumulativeReturn())

