# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

from pyalgotrade import broker

######################################################################
## Exceptions

class NotEnoughCash(Exception):
	def __init__(self):
		Exception.__init__(self, "Not enough cash")


######################################################################
## Orders
class MarketOrder(broker.MarketOrder):
	def __init__(self, action, instrument, quantity, onClose, goodTillCanceled):
		broker.MarketOrder.__init__(self, action, instrument, quantity, goodTillCanceled)
		self.__onClose = onClose

	def __getPrice(self, broker, bar_):
		# Fill the order at the open or close price (as in NinjaTrader).
		if self.__onClose:
			if broker.getUseAdjustedValues():
				ret = bar_.getAdjClose()
			else:
				ret = bar_.getClose()
		else:
			if broker.getUseAdjustedValues():
				ret = bar_.getAdjOpen()
			else:
				ret = bar_.getOpen()
		return ret

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.__tryExecuteImpl(broker, bars)
			self.checkCanceled(bars)

	def __tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getPrice(broker_, bar_)
			broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class LimitOrder(broker.LimitOrder):
	def __getPrice(self, broker_, bar_):
		if broker_.getUseAdjustedValues():
			high = bar_.getAdjHigh()
			low = bar_.getAdjLow()
		else:
			high = bar_.getHigh()
			low = bar_.getLow()

		price = self.getPrice()
		if price >= low and price <= high:
			ret = price
		else:
			ret = None
		return ret

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.__tryExecuteImpl(broker, bars)
			self.checkCanceled(bars)

	def __tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getPrice(broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class StopOrder(broker.StopOrder):
	def __getPrice(self, broker_, bar_):
		if broker_.getUseAdjustedValues():
			high = bar_.getAdjHigh()
			low = bar_.getAdjLow()
		else:
			high = bar_.getHigh()
			low = bar_.getLow()

		# If the stop price is reached, fill the order at the trigger price (as in NinjaTrader).
		stopPrice = self.getPrice()
		if stopPrice >= low and stopPrice <= high:
			ret = stopPrice
		else:
			ret = None
		return ret

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.__tryExecuteImpl(broker, bars)
			self.checkCanceled(bars)

	def __tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getPrice(broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class StopLimitOrder(broker.StopLimitOrder):
	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.__tryExecuteImpl(broker, bars)
			self.checkCanceled(bars)

	def __tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())

			# Check if we have reached the stop price:
			high = bar_.getHigh()
			low = bar_.getLow()
			
			limitPrice = self.getPrice()
			stopPrice = self.getStopPrice()
			action = self.getAction()
			
			# Check if we have ever reached the stop price
			if self.isLimitOrderActive():
				if limitPrice >= low and action == broker.Order.Action.BUY:
					broker_.commitOrderExecution(self, limitPrice, self.getQuantity(), bar_.getDateTime())
				elif limitPrice <= high and action in (broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT):
					broker_.commitOrderExecution(self, limitPrice, self.getQuantity(), bar_.getDateTime())
			else:
				if stopPrice <= high and action == broker.Order.Action.BUY:
					self.setLimitOrderActive(True)
				elif stopPrice >= low and action in (broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT):
					self.setLimitOrderActive(True)
		except KeyError:
			pass

class ExecuteIfFilled(broker.ExecuteIfFilled):
	def tryExecute(self, broker, bars):
		if self.getIndependent().isFilled():
			self.getDependent().tryExecute(broker, bars)
		elif self.getIndependent().isCanceled(): 
			self.getDependent().cancel()

######################################################################
## Broker

class Broker(broker.BasicBroker):
	"""Class responsible for processing orders.

	:param cash: The initial amount of cash.
	:type cash: int or float.
	:param barFeed: The bar feed that will provide the bars.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
	:param commission: An object responsible for calculating order commissions.
	:type commission: :class:`Commission`
	"""

	def __init__(self, cash, barFeed, commission = None):
		broker.BasicBroker.__init__(self, cash, commission)
		self.__shares = {}
		self.__pendingOrders = []
		self.__useAdjustedValues = False

		# It is VERY important that the broker subscribes to barfeed events before the strategy.
		barFeed.getNewBarsEvent().subscribe(self.onBars)
		self.__barFeed = barFeed

	def getUseAdjustedValues(self):
		return self.__useAdjustedValues

	def setUseAdjustedValues(self, useAdjusted):
		self.__useAdjustedValues = useAdjusted

	def getPendingOrders(self):
		return self.__pendingOrders

	def getShares(self, instrument):
		"""Returns the number of shares for an instrument."""
		self.__shares.setdefault(instrument, 0)
		return self.__shares[instrument]

	def getValue(self, bars):
		"""Returns the portfolio value (cash + shares) for the given bars prices.

		:param bars: The bars to use to calculate share values.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		ret = self.getCash()
		for instrument, shares in self.__shares.iteritems():
			if self.getUseAdjustedValues():
				instrumentPrice = bars.getBar(instrument).getAdjClose()
			else:
				instrumentPrice = bars.getBar(instrument).getClose()
			ret += instrumentPrice * shares
		return ret

	# Tries to commit an order execution. Returns True if the order was commited, or False is there is not enough cash.
	def commitOrderExecution(self, order, price, quantity, dateTime):
		if order.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			cost = price * quantity * -1
			assert(cost < 0)
			sharesDelta = quantity
		elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			cost = price * quantity
			assert(cost > 0)
			sharesDelta = quantity * -1
		else:
			assert(False)

		ret = False
		commission = self.getCommission().calculate(order, price, quantity)
		cost -= commission
		resultingCash = self.getCash() + cost

		# Check that we're ok on cash after the commission.
		if resultingCash >= 0:
			# Commit the order execution.
			self.setCash(resultingCash)
			self.__shares[order.getInstrument()] = self.getShares(order.getInstrument()) + sharesDelta
			ret = True

			# Update the order.
			orderExecutionInfo = broker.OrderExecutionInfo(price, commission, dateTime)
			order.setExecuted(orderExecutionInfo)

		return ret

	def placeOrder(self, order):
		"""Submits an order.

		:param order: The order to submit.
		:type order: :class:`Order`.
		"""

		if not order.isAccepted() or order in self.__pendingOrders:
			raise Exception("Can't place the same order twice")

		self.__pendingOrders.append(order)

	def onBars(self, bars):
		pendingOrders = self.__pendingOrders
		self.__pendingOrders = []

		for order in pendingOrders:
			if order.isAccepted():
				order.tryExecute(self, bars)
				if order.isAccepted():
					self.__pendingOrders.append(order)
				else:
					self.getOrderUpdatedEvent().emit(self, order)
			else:
				self.getOrderUpdatedEvent().emit(self, order)

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

	def stopDispatching(self):
		# If there are no more events in the barfeed, then there is nothing left for us to do since all processing took
		# place while processing barfeed events.
		return self.__barFeed.stopDispatching()

	def dispatch(self):
		# All events were already emitted while handling barfeed events.
		pass
	
	def createMarketOrder(self, action, instrument, quantity, onClose, goodTillCanceled):
		return MarketOrder(action, instrument, quantity, onClose, goodTillCanceled)

	def createLimitOrder(self, action, instrument, price, quantity, goodTillCanceled):
		return LimitOrder(action, instrument, price, quantity, goodTillCanceled)

	def createStopOrder(self, action, instrument, triggerPrice, quantity, goodTillCanceled):
		return StopOrder(action, instrument, triggerPrice, quantity, goodTillCanceled)

	def createStopLimitOrder(self, action, instrument, triggerPrice, price, quantity, goodTillCanceled):
		return StopLimitOrder(action, instrument, price, triggerPrice, quantity, goodTillCanceled)

	def createExecuteIfFilled(self, dependent, independent):
		return(ExecuteIfFilled(dependent, independent))

# vim: noet:ci:pi:sts=0:sw=4:ts=4
