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

from pyalgotrade import observer

######################################################################
## Commissions

class Commission:
	def calculate(self, order, price, quantity):
		raise NotImplementedError()

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

	:param type_: The order type
	:type type_: :class:`Order.Type`
	:param action: The order action.
	:type action: :class:`Order.Action`
	:param instrument: Instrument identifier.
	:type instrument: string.
	:param price: The price associated with the order. The meaning of this variable depends on the order type.
	:type price: float
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
		BUY			= 1
		SELL		= 2
		SELL_SHORT	= 3

	class State:
		ACCEPTED		= 1
		CANCELED		= 2
		FILLED			= 3

	class Type:
		MARKET				= 1
		LIMIT				= 2
		STOP				= 3
		STOP_LIMIT			= 4
		EXEC_IF_FILLED		= 5

	def __init__(self, type_, action, instrument, price, quantity, goodTillCanceled = False):
		self.__type = type_
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
	"""

	def __init__(self, action, instrument, quantity, goodTillCanceled = False):
		price = 0
		Order.__init__(self, Order.Type.MARKET, action, instrument, price, quantity, goodTillCanceled)

class LimitOrder(Order):
	"""
	An :class:`Order` subclass that instructs the broker to buy or sell the stock at a particular price.
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
		
	def getStopPrice(self):
		"""Returns orders stop price."""
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
class ExecuteIfFilled:
	def __init__(self, dependent, independent):
		self.__type = Order.Type.EXEC_IF_FILLED
		self.__dependent = dependent
		self.__independent = independent

	def getType(self):
		return self.__type

	def getDependent(self):
		return self.__dependent

	def getIndependent(self):
		return self.__independent

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
## BasicBroker
class BasicBroker:
	def __init__(self, cash, commission=None):
		assert(cash >= 0)
		self.__cash = cash

		if commission is None:
			self.__commission = NoCommission()
		else:
			self.__commission = commission
		
		self.__orderUpdatedEvent = observer.Event()

	def getOrderUpdatedEvent(self):
		return self.__orderUpdatedEvent
	
	def getCash(self):
		"""Returns the amount of cash."""
		return self.__cash

	def setCash(self, cash):
		"""Sets the amount of cash."""
		self.__cash = cash

	def getCommission(self):
		"""Returns the commission instance."""
		return self.__commission

	def setCommission(self, commission):
		"""Sets the commission instance."""
		self.__commission = commission

	def start(self):
		raise NotImplementedError()

	def stop(self):
		raise NotImplementedError()

	def join(self):
		raise NotImplementedError()

	# Return True if there are not more events to dispatch.
	def stopDispatching(self):
		raise NotImplementedError()

	# Dispatch events.
	def dispatch(self):
		raise NotImplementedError()
	
	def placeOrder(self, order):
		"""Submits an order.

		:param order: The order to submit.
		:type order: :class:`Order`.
		"""
		raise NotImplementedError()
	
	def createLongMarketOrder(self, instrument, quantity, goodTillCanceled=False):
		raise NotImplementedError()

	def createShortMarketOrder(self, instrument, quantity, goodTillCanceled=False):
		raise NotImplementedError()

	def createLongLimitOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		raise NotImplementedError()

	def createShortLimitOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		raise NotImplementedError()

	def createLongStopOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		raise NotImplementedError()

	def createShortStopOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		raise NotImplementedError()

	def createLongStopLimitOrder(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False): 
		raise NotImplementedError()

	def createShortStopLimitOrder(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False): 
		raise NotImplementedError()
	
	def createExecuteIfFilled(self, dependent, independent):
		raise NotImplementedError()

# vim: noet:ci:pi:sts=0:sw=4:ts=4
