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

# Helper class to calculate returns and profit/loss.
class ReturnsCalculator:
	def __init__(self):
		self.__buyQty = 0
		self.__buyTotal = 0
		self.__sellQty = 0
		self.__sellTotal = 0
		self.__cost = 0
		self.__commissions = 0

	def __updateCost(self, quantity, price):
		currentPos = self.__buyQty - self.__sellQty
		cost = 0

		if currentPos > 0: # Current position is long
			if quantity > 0: # Increase long position
				cost = quantity * price
			else:
				diff = currentPos + quantity
				if diff < 0: # Entering a short position
					cost = abs(diff) * price
		elif currentPos < 0: # Current position is short
			if quantity < 0: # Increase short position
				cost = abs(quantity) * price
			else:
				diff = currentPos + quantity
				if diff > 0: # Entering a long position
					cost = diff * price
		else:
			cost = abs(quantity) * price
		self.__cost += cost

	def getCost(self):
		return self.__cost

	def buy(self, quantity, price, commission = 0):
		self.__updateCost(quantity, price)
		self.__buyQty += quantity
		self.__buyTotal += quantity*price
		self.__commissions += commission

	def sell(self, quantity, price, commission = 0):
		self.__updateCost(quantity*-1, price)
		self.__sellQty += quantity
		self.__sellTotal += quantity*price
		self.__commissions += commission

	def getCommissions(self):
		return self.__commissions

	def __getBuySellAmounts(self, price):
		if self.__buyQty == self.__sellQty:
			buyTotal = self.__buyTotal
			sellTotal = self.__sellTotal
		elif self.__buyQty > self.__sellQty:
			buyTotal = self.__buyTotal
			sellTotal = self.__sellTotal + (self.__buyQty - self.__sellQty) * price
		else:
			buyTotal = self.__buyTotal + (self.__sellQty - self.__buyQty) * price
			sellTotal = self.__sellTotal
		return (buyTotal, sellTotal)

	def getReturn(self, price, includeCommissions = True):
		ret = 0
		pl = self.getProfitLoss(price, includeCommissions)
		cost = self.getCost()
		if cost != 0:
			ret = pl / float(cost)
		return ret

	def getProfitLoss(self, price, includeCommissions = True):
		buy, sell = self.__getBuySellAmounts(price)
		ret = 0
		if buy != 0:
			if includeCommissions:
				commission = self.__commissions
			else:
				commission = 0
			ret = sell - buy - commission
		return ret

	def updatePrice(self, price):
		if self.__buyQty == self.__sellQty:
			self.__buyQty = 0
			self.__sellQty = 0
		elif self.__buyQty > self.__sellQty:
			self.__buyQty -= self.__sellQty
			self.__sellQty = 0
		else:
			self.__sellQty -= self.__buyQty
			self.__buyQty = 0

		self.__buyTotal = self.__buyQty * price
		self.__sellTotal = self.__sellQty * price
		self.__commissions = 0
		self.__cost = abs(self.__buyQty - self.__sellQty) * price

class ReturnsAnalyzerBase(stratanalyzer.StrategyAnalyzer):
	def __init__(self, includeCommissions = True):
		self.__cumRet = 0
		self.__lastBars = {} # Last Bar per instrument.
		self.__returnCalculators = {}
		self.__useAdjClose = False
		self.__includeCommissions = includeCommissions

	def attached(self, strat):
		strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)
		self.__useAdjClose = strat.getBroker().getUseAdjustedValues()

	def __onOrderUpdate(self, broker_, order):
		# Only interested in filled orders.
		if not order.isFilled():
			return

		# Get or create the returns calculator for this instrument.
		try:
			retCalculator = self.__returnCalculators[order.getInstrument()]
		except KeyError:
			retCalculator = ReturnsCalculator()
			self.__returnCalculators[order.getInstrument()] = retCalculator

		# Update the returns calculator for this order.
		if order.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			commission = order.getExecutionInfo().getCommission()
			retCalculator.buy(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commission)
		elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			commission = order.getExecutionInfo().getCommission()
			retCalculator.sell(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commission)
		else: # Unknown action
			assert(False)

	def onReturns(self, bars, netReturn, cumulativeReturn):
		raise NotImplementedError()

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
		totalCommissions = 0

		# Calculate net return.
		for instrument, retCalculator in self.__returnCalculators.iteritems():
			price = self.__getPrice(instrument, bars)
			if price != None:
				totalPL += retCalculator.getProfitLoss(price, self.__includeCommissions)
				totalCost += retCalculator.getCost()
				retCalculator.updatePrice(price) 

		if totalCost == 0:
			netReturn = 0
		else:
			netReturn = totalPL / float(totalCost)

		# Calculate cumulative return.
		self.__cumRet = (1 + self.__cumRet) * (1 + netReturn) - 1

		# Notify the returns
		self.onReturns(bars, netReturn, self.__cumRet)

		# Keep track of the last bar for each instrument.
		for instrument in bars.getInstruments():
			self.__lastBars[instrument] = bars.getBar(instrument)

class ReturnsAnalyzer(ReturnsAnalyzerBase):
	def __init__(self):
		ReturnsAnalyzerBase.__init__(self)
		self.__netReturns = []

	def onReturns(self, bars, netReturn, cumulativeReturn):
		dateTime = bars.getDateTime()
		self.__netReturns.append((dateTime, netReturn))

	def getNetReturns(self):
		return self.__netReturns

