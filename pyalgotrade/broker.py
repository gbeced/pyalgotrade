# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

import observer

######################################################################
## Exceptions

class NotEnoughCash(Exception):
	def __init__(self):
		Exception.__init__(self, "Not enough cash")

######################################################################
## Commissions

class Commission:
	def calculate(self, order, price, quantity):
		raise Exception("Not implemented")

class NoCommission(Commission):
	def calculate(self, order, price, quantity):
		return 0

class FixedCommission(Commission):
	def __init__(self, cost):
		self.__cost = cost

	def calculate(self, order, price, quantity):
		return self.__cost

######################################################################
## Orders
## http://stocks.about.com/od/tradingbasics/a/markords.htm

class Order:
	"""Base class for orders. 

	:param action: The order action.
	:param instrument: Instrument identifier.
	:type instrument: string.
	:param quantity: Order quantity.
	:type quantity: int.
	:param goodTillCanceled: True if the order is good till canceled. Orders that are not filled by the time the session closes will be will be automatically canceled if they were not set as good till canceled.
	:type goodTillCanceled: boolean.

	.. note::

		Valid **action** parameter values are:

		 * Order.Action.BUY
		 * Order.Action.SELL
		 * Order.Action.SELL_SHORT

		This is a base class and should not be used directly.
	"""

	class Action:
		BUY					= 1
		SELL				= 2
		SELL_SHORT			= 3

	class State:
		ACCEPTED			= 1
		CANCELED			= 2
		FILLED				= 3

	class Type:
		MARKET				= 1
		LIMIT				= 2
		STOP				= 3
		STOP_LIMIT			= 4
		EXEC_IF_FILLED		= 5

	def __init__(self, type, action, instrument, price, quantity, goodTillCanceled = False):
		self.__type = type
		self.__action = action
		self.__instrument = instrument
		self.__price = price
		self.__quantity = quantity
		self.__executionInfo = None
		self.__goodTillCanceled = goodTillCanceled
		self.__state = Order.State.ACCEPTED

	def getType(self):
		"""Returns the order type"""
		return self.__type

	def getAction(self):
		"""Returns the order action."""
		return self.__action

	def getState(self):
		"""Returns the order state.

		Valid order states are:
		 * Order.State.ACCEPTED (the initial state).
		 * Order.State.CANCELED
		 * Order.State.FILLED
		"""
		return self.__state

	def isAccepted(self):
		"""Returns True if the order state is Order.State.ACCEPTED."""
		return self.__state == Order.State.ACCEPTED

	def isCanceled(self):
		"""Returns True if the order state is Order.State.CANCELED."""
		return self.__state == Order.State.CANCELED

	def isFilled(self):
		"""Returns True if the order state is Order.State.FILLED."""
		return self.__state == Order.State.FILLED

	def cancel(self):
		"""Cancels an accepted order. If the order is filled an Exception is raised."""
		if self.isFilled():
			raise Exception("Can't cancel order that has already been processed")
		self.__state = Order.State.CANCELED

	def getInstrument(self):
		"""Returns the instrument identifier."""
		return self.__instrument

	def getPrice(self):
		"""Returns order price."""
		return self.__price

	def getQuantity(self):
		"""Returns the quantity."""
		return self.__quantity

	def getGoodTillCanceled(self):
		"""Returns True if the order is good till canceled."""
		return self.__goodTillCanceled

	def setExecuted(self, orderExecutionInfo):
		self.__executionInfo = orderExecutionInfo
		self.__state = Order.State.FILLED

	def checkCanceled(self, bars):
		# If its the last bar of the session and the order is not GTC, then cancel it.
		if self.isAccepted() and self.getGoodTillCanceled() == False and bars.getBar(self.__instrument).getSessionClose():
			self.__state = Order.State.CANCELED

	def getExecutionInfo(self):
		"""Returns the order execution info if the order was filled, or None otherwise.

		:rtype: :class:`OrderExecutionInfo`.
		"""
		return self.__executionInfo

class MarketOrder(Order):
	"""
	An :class:`Order` subclass that instructs the broker to buy or sell the stock immediately at the prevailing price, whatever that may be.
	If useClosingPrice is set to False then the opening price will be used to fill the order, otherwise the closing price will be used.
	"""

	def __init__(self, action, instrument, quantity, goodTillCanceled = False, useClosingPrice = False):
		price = 0
		Order.__init__(self, Order.Type.MARKET, action, instrument, price, quantity, goodTillCanceled)
		self.__useClosingPrice = useClosingPrice

	def getUseClosingPrice(self):
		return self.__useClosingPrice

class LimitOrder(Order):
	"""
	An :class:`Order` subclass that instructs the broker to buy or sell the stock stock at a particular price.
	The purchase or sale will not happen unless you get your price.
	"""

	def __init__(self, action, instrument, price, quantity, goodTillCanceled = False):
		Order.__init__(self, Order.Type.LIMIT, action, instrument, price, quantity, goodTillCanceled)


class StopOrder(Order):
	"""
	An :class:`Order` subclass that gives your broker a price trigger that protects you from a big drop in a stock.
		You enter a stop loss order at a point below the current market price. If the stock falls to this price point, 
		the stop loss order becomes a market order and your broker sells the stock. If the stock stays level or rises, 
		the stop loss order does nothing.
	"""

	def __init__(self, action, instrument, price, quantity, goodTillCanceled = False):
		Order.__init__(self, Order.Type.STOP, action, instrument, price, quantity, goodTillCanceled)

class StopLimitOrder(Order):
	"""
	An :class:`Order` subclass that gives your broker a price trigger that protects you from a big drop in a stock.
		You enter a stop loss order at a point below the current market price. If the stock falls to this price point, 
		the stop loss order becomes a limit order with the defined limit price. If the stock stays level or rises, 
		the stop loss order does nothing.
	"""
	def __init__(self, action, instrument, limitPrice, stopPrice, quantity, goodTillCanceled = False):
		Order.__init__(self, Order.Type.STOP_LIMIT, action, instrument, limitPrice, quantity, goodTillCanceled)
		self.__stopPrice = stopPrice
		self.__limitOrderActive = False # Set to true when the limit order is activated (stop price is hit)
		
	def getStop(self):
		"""Returns orders limit price."""
		return self.__stopPrice

	def setLimitOrderActive(self, limitOrderActive):
		"""Sets the Limit Order Active boolean variable:
		Indicates if the Stop price is broken and the Limit Order is
		active on the market."""
		self.__limitOrderActive = limitOrderActive

	def isLimitOrderActive(self):
		"""Returns the Limit Order Active boolean variable"""
		return self.__limitOrderActive


# Special order wrapper that executes an order (dependent) only if another order (independent) was filled.
class ExecuteIfFilled(Order):
	def __init__(self, dependent, independent):
		Order.__init__(self, Order.Type.EXEC_IF_FILLED, action='', instrument='', quantity=0, price=0, goodTillCanceled=True)
		self.__dependent = dependent
		self.__independent = independent

	def getDependent(self):
		return self.__dependent

	def getIndependent(self):
		return self.__independent

	def tryExecute(self, broker, bars):
		if self.__independent.isFilled():
			self.__dependent.tryExecute(broker, bars)
		elif self.__independent.isCanceled(): 
			self.__dependent.cancel()

	def __getattr__(self, name):
		return getattr(self.__dependent, name) 

class OrderExecutionInfo:
	"""Execution information for a filled order."""
	def __init__(self, price, commission, dateTime):
		self.__price = price
		self.__commission = commission
		self.__dateTime = dateTime

	def getPrice(self):
		"""Returns execution price."""
		return self.__price

	def getCommission(self):
		"""Returns commission applied."""
		return self.__commission

	def getDateTime(self):
		"""Returns the :class:`datatime.datetime` when the order was executed."""
		return self.__dateTime

######################################################################
## Broker

class BasicBroker:
	"""Class responsible for processing orders.
	:param cash: The initial amount of cash.
	:type cash: int or float.
	:param commission: An object responsible for calculating order commissions.
	:type commission: :class:`Commission`
	"""
	def __init__(self, cash, commission = None):
		assert(cash >= 0)
		self.__cash = cash
		if commission is None:
			self.__commission = NoCommission()
		else:
			self.__commission = commission
		self.__orderUpdatedEvent = observer.Event()
	
	def getCash(self):
		"""Returns the amount of cash."""
		return self.__cash

	def setCash(self, cash):
		self.__cash = cash

	def setCommission(self, commission):
		self.__commission = commission
	
	def getCommission(self):
		return self.__commission

	def getOrderUpdatedEvent(self):
		return self.__orderUpdatedEvent

	def placeOrder(self, order):
		"""Submits an order.

		:param order: The order to submit.
		:type order: :class:`Order`.
		"""
		raise Exception("Not implemented")
	
	def onBars(self, bars):
		raise Exception("Not implemented")

class Broker(BasicBroker):
	"""Class responsible for processing orders.
	:param cash: The initial amount of cash.
	:type cash: int or float.
	:param commission: An object responsible for calculating order commissions.
	:type commission: :class:`Commission`
	"""
	def __init__(self, cash, commission = None):
		BasicBroker.__init__(self, cash, commission)

		self.__pendingOrders = []
		self.__useAdjustedValues = False
		self.__shares = {}

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
		if order.getAction() == Order.Action.BUY:
			cost = price * quantity * -1
			assert(cost < 0)
			sharesDelta = quantity
		elif order.getAction() in [Order.Action.SELL, Order.Action.SELL_SHORT]:
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
			orderExecutionInfo = OrderExecutionInfo(price, commission, dateTime)
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


	def __processOrder(self, order, bars):
		orderType = order.getType()

		if orderType != Order.Type.EXEC_IF_FILLED:
			bar_ = bars.getBar(order.getInstrument())
			quantity = order.getQuantity()
			dateTime = bar_.getDateTime()
		
		if orderType == Order.Type.MARKET:
			# Try to fill the order at the Open price.

			if order.getUseClosingPrice():
				if self.getUseAdjustedValues():
					price = bar_.getAdjClose()
				else:
					price =  bar_.getClose()
			else:
				if self.getUseAdjustedValues():
					price = bar_.getAdjOpen()
				else:
					price =  bar_.getOpen()

			self.commitOrderExecution(order, price, quantity, dateTime)

			order.checkCanceled(bars)
		elif orderType == Order.Type.LIMIT:
			# Check if we have reached the limit price:
			high = bar_.getHigh()
			low = bar_.getLow()

			price = order.getPrice()

			if low <= price <= high:
				# Limit price reached, mark the order executed
				self.commitOrderExecution(order, price, quantity, dateTime)
				order.checkCanceled(bars)
		elif orderType == Order.Type.STOP:
			# Check if we have reached the stop price:
			high = bar_.getHigh()
			low = bar_.getLow()
			close = bar_.getClose()

			price = order.getPrice()

			if low <= price <= high:
				# Stop price reached, initiate a market order:
				# Fill the order with the close price
				self.commitOrderExecution(order, close, quantity, dateTime)
				order.checkCanceled(bars)

		elif orderType == Order.Type.STOP_LIMIT:
			# Check if we have reached the stop price:
			high = bar_.getHigh()
			low = bar_.getLow()
			close = bar_.getClose()
			
			limitPrice = order.getPrice()
			stopPrice = order.getStopPrice()
			
			# Check if we have reached the stop price or if the Limit Order is active
			if (low <= stopPrice <= high) or order.isLimitOrderActive():
				# Stop price reached, initiate a limit order:
				# Mark the request as Limit Order Active. This ensures that if the 
				# Stop price is broken once the limit order will be active in the book.
				order.setLimitOrderActive(True)

				# Fill the order with the close price
				if low <= limitPrice <= high:
					self.commitOrderExecution(order, close, limitPrice, quantity, dateTime)
					order.checkCanceled(bars)

		elif orderType == Order.Type.EXEC_IF_FILLED:
			dependent = order.getDependent()
			independent = order.getIndependent()

			if independent.isFilled():
				self.__processOrder(dependent, bars)
			elif independent.isCanceled(): 
				dependent.cancel()

		else:
			raise Exception("Invalid Order Type at Broker.__processOrder()")
			

	def onBars(self, bars):
		pendingOrders = self.__pendingOrders
		self.__pendingOrders = []

		for order in pendingOrders:
			if order.isAccepted():
				self.__processOrder(order, bars)
								
				if order.isAccepted():
					self.__pendingOrders.append(order)
				else:
					self.getOrderUpdatedEvent().emit(self, order)
			else:
				self.getOrderUpdatedEvent().emit(self, order)

	# TBD: Populate these functions
	def createLongMarketOrder(self): pass
	def createShortMarketOrder(self): pass
	def createLongLimitOrder(self): pass
	def createShortLimitOrder(self): pass
	def createLongStopOrder(self): pass
	def createShortStopOrder(self): pass
	def createLongStopLimitOrder(self): pass
	def createShortStopLimitOrder(self): pass
# vim: noet:ci:pi:sts=0:sw=4:ts=4
