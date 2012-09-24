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

class ReturnsCalculator:
	def __init__(self):
		self.__buyQty = 0
		self.__buyTotal = 0
		self.__sellQty = 0
		self.__sellTotal = 0
		self.__commisions = 0

	def buy(self, quantity, price, commision = 0):
		self.__buyQty += quantity
		self.__buyTotal += quantity*price
		self.__commisions += commision

	def sell(self, quantity, price, commision = 0):
		self.__sellQty += quantity
		self.__sellTotal += quantity*price
		self.__commisions += commision

	def getCommisions(self):
		return self.__commisions

	def getBuySellAmounts(self, price):
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

	def calculateReturn(self, price, includeCommisions = True):
		buy, sell = self.getBuySellAmounts(price)
		if buy == 0:
			return 0
		else:
			if includeCommisions:
				commision = self.__commisions
			else:
				commision = 0
			return (sell - buy - commision) / float(buy)

	def update(self, price):
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
		self.__commisions = 0

class ReturnsAnalyzerBase(stratanalyzer.StrategyAnalyzer):
	def __init__(self, includeCommisions = True):
		self.__cumRet = 0
		self.__lastBars = {} # Last Bar per instrment.
		self.__returnCalculators = {}
		self.__useAdjClose = False
		self.__includeCommisions = includeCommisions

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
			commision = order.getExecutionInfo().getCommission()
			retCalculator.buy(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commision)
		elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			commision = order.getExecutionInfo().getCommission()
			retCalculator.sell(order.getExecutionInfo().getQuantity(), order.getExecutionInfo().getPrice(), commision)
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
		totalBought = 0
		totalSold = 0
		totalCommisions = 0

		# Calculate net return.
		for instrument, retCalculator in self.__returnCalculators.iteritems():
			price = self.__getPrice(instrument, bars)
			if price != None:
				bought, sold = retCalculator.getBuySellAmounts(price)
				if self.__includeCommisions:
					totalCommisions += retCalculator.getCommisions()
				totalBought += bought
				totalSold += sold
				retCalculator.update(price) 

		if totalBought == 0:
			netReturn = 0
		else:
			netReturn = (totalSold - totalBought - totalCommisions) / float(totalBought)

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

