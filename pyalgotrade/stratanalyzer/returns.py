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
		self.__updateCost(quantity, price)
		self.__cash += quantity * -1 * price
		self.__shares += quantity
		self.__commissions += commission

	def sell(self, quantity, price, commission = 0):
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
		self.__lastBars = {} # Last Bar per instrument.
		self.__posTrackers = {}
		self.__useAdjClose = False
		self.__event = observer.Event()

	@classmethod
	def getOrCreateShared(cls, strat):
		name = cls.__name__
		# Get or create the shared ReturnsAnalyzerBase.
		ret = strat.getNamedAnalyzer(name)
		if ret == None:
			ret = ReturnsAnalyzerBase()
			strat.attachAnalyzerEx(ret, name)
		return ret

	def attached(self, strat):
		strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)
		self.__useAdjClose = strat.getBroker().getUseAdjustedValues()

	# An event will be notified when return are calculated at each bar. The hander should receive 2 parameters:
	# 1: This analyzer's instance
	# 2: The bars
	def getEvent(self):
		return self.__event

	def getNetReturn(self):
		return self.__netRet

	def getCumulativeReturn(self):
		return self.__cumRet

	def __onOrderUpdate(self, broker_, order):
		# Only interested in filled orders.
		if not order.isFilled():
			return

		# Get or create the returns calculator for this instrument.
		try:
			posTracker = self.__posTrackers[order.getInstrument()]
		except KeyError:
			posTracker = PositionTracker()
			self.__posTrackers[order.getInstrument()] = posTracker

		# Update the returns calculator for this order.
		if order.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			commission = order.getExecutionInfo().getCommission()
			posTracker.buy(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commission)
		elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			commission = order.getExecutionInfo().getCommission()
			posTracker.sell(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commission)
		else: # Unknown action
			assert(False)

	def __getPrice(self, instrument, bars):
		ret = None
		bar = bars.getBar(instrument)
		if bar == None:
			bar = self.__lastBars.get(instrument, None)
		if bar != None:
			if self.__useAdjClose:
				ret = bar.getAdjClose()
			else:
				ret = bar.getClose()
		return ret

	def beforeOnBars(self, strat, bars):
		totalPL = 0
		totalCost = 0

		# Calculate net return.
		for instrument, posTracker in self.__posTrackers.iteritems():
			price = self.__getPrice(instrument, bars)
			if price != None:
				totalPL += posTracker.getNetProfit(price, True)
				totalCost += posTracker.getCost()
				posTracker.update(price) 

		if totalCost == 0:
			netReturn = 0
		else:
			netReturn = totalPL / float(totalCost)
		self.__netRet = netReturn

		# Calculate cumulative return.
		self.__cumRet = (1 + self.__cumRet) * (1 + netReturn) - 1

		# Notify that new returns are available.
		self.__event.emit(self, bars)

		# Keep track of the last bar for each instrument.
		for instrument in bars.getInstruments():
			self.__lastBars[instrument] = bars.getBar(instrument)

class ReturnsAnalyzer(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates returns and cumulative returns."""
	def __init__(self):
		self.__netReturns = {}
		self.__cumReturns = {}
		self.__lastNetRet = 0
		self.__lastCumRet = 0 

	def beforeAttach(self, strat):
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		dateTime = bars.getDateTime()
		self.__netReturns[dateTime] = returnsAnalyzerBase.getNetReturn()
		self.__cumReturns[dateTime] = returnsAnalyzerBase.getCumulativeReturn()
		self.__lastNetRet = returnsAnalyzerBase.getNetReturn()
		self.__lastCumRet = returnsAnalyzerBase.getCumulativeReturn()

	def getNetReturns(self):
		"""Returns a dictionary with the net returns for each bar."""
		return self.__netReturns

	def getCumulativeReturns(self):
		"""Returns a dictionary with the cumulative returns for each bar."""
		return self.__cumReturns

	def getLastNetReturn(self):
		"""Returns the net return for the last bar."""
		return self.__lastNetRet

	def getLastCumulativeReturn(self):
		"""Returns the cumulative return up to the last bar."""
		return self.__lastCumRet

