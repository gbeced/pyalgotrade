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
		 * Order.Action.BUY_TO_COVER
		 * Order.Action.SELL
		 * Order.Action.SELL_SHORT

		This is a base class and should not be used directly.
	"""

	class Action:
		BUY				= 1
		BUY_TO_COVER	= 2
		SELL			= 3
		SELL_SHORT		= 4

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

	def getExecutionInfo(self):
		"""Returns the order execution info if the order was filled, or None otherwise.

		:rtype: :class:`OrderExecutionInfo`.
		"""
		return self.__executionInfo
	
class MarketOrder(Order):
	def __init__(self, action, instrument, quantity, goodTillCanceled = False):
		price = 0
		Order.__init__(self, Order.Type.MARKET, action, instrument, price, quantity, goodTillCanceled)

class LimitOrder(Order):
	def __init__(self, action, instrument, limitPrice, quantity, goodTillCanceled = False):
		Order.__init__(self, Order.Type.LIMIT, action, instrument, limitPrice, quantity, goodTillCanceled)

class StopOrder(Order):
	def __init__(self, action, instrument, stopPrice, quantity, goodTillCanceled = False):
		Order.__init__(self, Order.Type.STOP, action, instrument, stopPrice, quantity, goodTillCanceled)

class StopLimitOrder(Order):
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
	
	def createMarketOrder(self, action, instrument, quantity, onClose, goodTillCanceled):
		"""Creates a Market order.
		A market order is an order to buy or sell a stock at the best available price.
		Generally, this type of order will be executed immediately. However, the price at which a market order will be executed
		is not guaranteed.

		:param action: The order action.
		:type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: Order quantity.
		:type quantity: int.
		:param onClose: True if the order should be filled as close to the closing price as possible (Market-On-Close order).
		:type onClose: boolean.
		:param goodTillCanceled: True if the order is good till canceled. Orders that are not filled by the time the session closes will be will be automatically canceled if they were not set as good till canceled.
		:type goodTillCanceled: boolean.
		"""
		raise NotImplementedError()

	def createLimitOrder(self, action, instrument, limitPrice, quantity, goodTillCanceled): 
		"""Creates a Limit order.
		A limit order is an order to buy or sell a stock at a specific price or better.
		A buy limit order can only be executed at the limit price or lower, and a sell limit order can only be executed at the
		limit price or higher.		

		:param action: The order action.
		:type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param limitPrice: The order price.
		:type limitPrice: float
		:param quantity: Order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the order is good till canceled. Orders that are not filled by the time the session closes will be will be automatically canceled if they were not set as good till canceled.
		:type goodTillCanceled: boolean.
		"""
		raise NotImplementedError()

	def createStopOrder(self, action, instrument, stopPrice, quantity, goodTillCanceled): 
		"""Creates a Stop order.
		A stop order, also referred to as a stop-loss order, is an order to buy or sell a stock once the price of the stock
		reaches a specified price, known as the stop price.
		When the stop price is reached, a stop order becomes a market order.
		A buy stop order is entered at a stop price above the current market price. Investors generally use a buy stop order
		to limit a loss or to protect a profit on a stock that they have sold short.
		A sell stop order is entered at a stop price below the current market price. Investors generally use a sell stop order
		to limit a loss or to protect a profit on a stock that they own.

		:param action: The order action.
		:type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param stopPrice: The trigger price.
		:type stopPrice: float
		:param quantity: Order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the order is good till canceled. Orders that are not filled by the time the session closes will be will be automatically canceled if they were not set as good till canceled.
		:type goodTillCanceled: boolean.
		"""
		raise NotImplementedError()

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity, goodTillCanceled): 
		"""Creates a Stop-Limit order.
		A stop-limit order is an order to buy or sell a stock that combines the features of a stop order and a limit order.
		Once the stop price is reached, a stop-limit order becomes a limit order that will be executed at a specified price
		(or better). The benefit of a stop-limit order is that the investor can control the price at which the order can be executed.

		:param action: The order action.
		:type action: Order.Action.BUY, or Order.Action.BUY_TO_COVER, or Order.Action.SELL or Order.Action.SELL_SHORT.
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param stopPrice: The trigger price.
		:type stopPrice: float
		:param limitPrice: The price for the limit order.
		:type limitPrice: float
		:param quantity: Order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the order is good till canceled. Orders that are not filled by the time the session closes will be will be automatically canceled if they were not set as good till canceled.
		:type goodTillCanceled: boolean.
		"""
		raise NotImplementedError()

	def createExecuteIfFilled(self, dependent, independent):
		raise NotImplementedError()

# vim: noet:ci:pi:sts=0:sw=4:ts=4
