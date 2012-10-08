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
## http://www.interactivebrokers.com/en/software/tws/usersguidebook/ordertypes/basic_order_types.htm

class Order:
	"""Base class for orders. 

	:param type_: The order type
	:type type_: :class:`Order.Type`
	:param action: The order action.
	:type action: :class:`Order.Action`
	:param instrument: Instrument identifier.
	:type instrument: string.
	:param quantity: Order quantity.
	:type quantity: int.

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

	def __init__(self, type_, action, instrument, quantity):
		self.__type = type_
		self.__action = action
		self.__instrument = instrument
		self.__quantity = quantity
		self.__executionInfo = None
		self.__goodTillCanceled = False
		self.__allOrNone = True
		self.__state = Order.State.ACCEPTED
		self.__dirty = False

	def isDirty(self):
		return self.__dirty

	def setDirty(self, dirty):
		self.__dirty = dirty

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

	def getInstrument(self):
		"""Returns the instrument identifier."""
		return self.__instrument

	def getQuantity(self):
		"""Returns the quantity."""
		return self.__quantity

	def setQuantity(self, quantity):
		"""Updates the quantity."""
		self.__quantity = quantity
		self.setDirty(True)

	def getGoodTillCanceled(self):
		"""Returns True if the order is good till canceled."""
		return self.__goodTillCanceled

	def setGoodTillCanceled(self, goodTillCanceled):
		"""Sets if the order should be good till canceled.
		Orders that are not filled by the time the session closes will be will be automatically canceled
		if they were not set as good till canceled

		:param goodTillCanceled: True if the order should be good till canceled.
		:type goodTillCanceled: boolean.
		"""
		self.__goodTillCanceled = goodTillCanceled
		self.setDirty(True)

	def getAllOrNone(self):
		"""Returns True if the order should be completely filled or else canceled."""
		return self.__allOrNone

	def setAllOrNone(self, allOrNone):
		"""Sets the All-Or-None property for this order.

		:param allOrNone: True if the order should be completely filled or else canceled.
		:type allOrNone: boolean.
		"""
		self.__allOrNone = allOrNone
		self.setDirty(True)

	def setExecuted(self, orderExecutionInfo):
		self.__executionInfo = orderExecutionInfo
		self.__state = Order.State.FILLED

	def setState(self, state):
		self.__state = state

	def getExecutionInfo(self):
		"""Returns the order execution info if the order was filled, or None otherwise.

		:rtype: :class:`OrderExecutionInfo`.
		"""
		return self.__executionInfo
	
class MarketOrder(Order):
	"""Base class for market orders.

	.. note::

		This is a base class and should not be used directly.
	"""

	def __init__(self, action, instrument, quantity, onClose):
		Order.__init__(self, Order.Type.MARKET, action, instrument, quantity)
		self.__onClose = onClose

	def getFillOnClose(self):
		"""Returns True if the order should be filled as close to the closing price as possible (Market-On-Close order)."""
		return self.__onClose

	def setFillOnClose(self, onClose):
		"""Sets if the order should be filled as close to the closing price as possible (Market-On-Close order)."""
		self.__onClose = onClose
		self.setDirty(True)

class LimitOrder(Order):
	"""Base class for limit orders.

	.. note::

		This is a base class and should not be used directly.
	"""

	def __init__(self, action, instrument, limitPrice, quantity):
		Order.__init__(self, Order.Type.LIMIT, action, instrument, quantity)
		self.__limitPrice = limitPrice

	def getLimitPrice(self):
		"""Returns the limit price."""
		return self.__limitPrice

	def setLimitPrice(self, limitPrice):
		"""Updates the limit price."""
		self.__limitPrice = limitPrice
		self.setDirty(True)

class StopOrder(Order):
	"""Base class for stop orders.

	.. note::

		This is a base class and should not be used directly.
	"""

	def __init__(self, action, instrument, stopPrice, quantity):
		Order.__init__(self, Order.Type.STOP, action, instrument, quantity)
		self.__stopPrice = stopPrice

	def getStopPrice(self):
		"""Returns the stop price."""
		return self.__stopPrice

	def setStopPrice(self, stopPrice):
		"""Updates the stop price."""
		self.__stopPrice = stopPrice
		self.setDirty(True)

class StopLimitOrder(Order):
	"""Base class for stop limit orders.

	.. note::

		This is a base class and should not be used directly.
	"""

	def __init__(self, action, instrument, limitPrice, stopPrice, quantity):
		Order.__init__(self, Order.Type.STOP_LIMIT, action, instrument, quantity)
		self.__limitPrice = limitPrice
		self.__stopPrice = stopPrice
		self.__limitOrderActive = False # Set to true when the limit order is activated (stop price is hit)
		
	def getLimitPrice(self):
		"""Returns the limit price."""
		return self.__limitPrice

	def setLimitPrice(self, limitPrice):
		"""Updates the limit price."""
		self.__limitPrice = limitPrice
		self.setDirty(True)

	def getStopPrice(self):
		"""Returns the stop price."""
		return self.__stopPrice

	def setStopPrice(self, stopPrice):
		"""Updates the stop price."""
		self.__stopPrice = stopPrice
		self.setDirty(True)

	def setLimitOrderActive(self, limitOrderActive):
		self.__limitOrderActive = limitOrderActive

	def isLimitOrderActive(self):
		"""Returns True if the limit order is active."""
		return self.__limitOrderActive

class OrderExecutionInfo:
	"""Execution information for a filled order."""
	def __init__(self, price, quantity, commission, dateTime):
		self.__price = price
		self.__quantity = quantity
		self.__commission = commission
		self.__dateTime = dateTime

	def getPrice(self):
		"""Returns the fill price."""
		return self.__price

	def getQuantity(self):
		"""Returns the quantity."""
		return self.__quantity

	def getCommission(self):
		"""Returns the commission applied."""
		return self.__commission

	def getDateTime(self):
		"""Returns the :class:`datatime.datetime` when the order was executed."""
		return self.__dateTime

######################################################################
## Base broker class
class Broker:
	"""Base class for brokers.

	.. note::

		This is a base class and should not be used directly.
	"""

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
		"""Returns the available cash."""
		return self.__cash

	def setCash(self, cash):
		"""Sets the available cash."""
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

		.. note::
			If the order is filled or canceled, an exception will be raised.
		"""
		raise NotImplementedError()
	
	def createMarketOrder(self, action, instrument, quantity, onClose = False):
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
		:param onClose: True if the order should be filled as close to the closing price as possible (Market-On-Close order). Default is False.
		:type onClose: boolean.
		:rtype: A :class:`MarketOrder` subclass.
		"""
		raise NotImplementedError()

	def createLimitOrder(self, action, instrument, limitPrice, quantity): 
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
		:rtype: A :class:`LimitOrder` subclass.
		"""
		raise NotImplementedError()

	def createStopOrder(self, action, instrument, stopPrice, quantity): 
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
		:rtype: A :class:`StopOrder` subclass.
		"""
		raise NotImplementedError()

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity): 
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
		:rtype: A :class:`StopLimitOrder` subclass.
		"""
		raise NotImplementedError()

	def cancelOrder(self, order):
		"""Requests an order to be canceled. If the order is filled an Exception is raised.

		:param order: The order to cancel.
		:type order: :class:`Order`.
		"""
		raise NotImplementedError()

# vim: noet:ci:pi:sts=0:sw=4:ts=4
