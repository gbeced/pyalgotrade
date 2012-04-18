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

import broker
import utils

class Position:
	"""Base class for positions. 

	:param entryOrder: The order used to enter the position.
	:type entryOrder: :class:`pyalgotrade.broker.Order`

	.. note::
		This is a base class and should not be used directly.
	"""

	def __init__(self, entryOrder):
		self.__entryOrder = entryOrder
		self.__exitOrder = None
		self.__exitOnSessionClose = False

	def setExitOnSessionClose(self, exitOnSessionClose):
		"""Set to True to automatically place the exit order in the last bar for the session."""
		self.__exitOnSessionClose = exitOnSessionClose

	def getExitOnSessionClose(self):
		"""Returns True if an order to exit the position should be automatically placed."""
		return self.__exitOnSessionClose

	def getEntryOrder(self):
		"""Returns the :class:`pyalgotrade.broker.Order` used to enter the position."""
		return self.__entryOrder

	def setExitOrder(self, exitOrder):
		self.__exitOrder = exitOrder

	def getExitOrder(self):
		"""Returns the :class:`pyalgotrade.broker.Order` used to exit the position. If this position hasn't been closed yet, None is returned."""
		return self.__exitOrder

	def getInstrument(self):
		"""Returns the instrument used for this position."""
		return self.__entryOrder.getInstrument()

	def getQuantity(self):
		"""Returns the number of shares used to enter this position."""
		return self.__entryOrder.getQuantity()

	def close(self, price, broker_):
		assert(self.getExitOrder() == None or self.getExitOrder().isCanceled())
		closeOrder = self.buildExitOrder(price)
		broker_.placeOrder(closeOrder)
		self.setExitOrder(closeOrder)

	def checkExitOnSessionClose(self, bars, broker_):
		ret = None
		try:
			if self.__exitOnSessionClose and self.__exitOrder == None and bars.getBar(self.getInstrument()).getSessionClose() == True:
				assert(self.getEntryOrder() != None)
				ret = self.buildExitOnSessionCloseOrder()
				ret = broker.ExecuteIfFilled(ret, self.getEntryOrder())
				broker_.placeOrder(ret)
				self.setExitOrder(ret)
		except KeyError:
			pass

		return ret

	def getResult(self):
		"""Returns the ratio between the order prices. **It doesn't include commisions**."""
		if not self.getEntryOrder().isFilled():
			raise Exception("Position not opened yet")
		if self.getExitOrder() == None or not self.getExitOrder().isFilled():
			raise Exception("Position not closed yet")
		return self.getResultImpl()

	def getResultImpl(self):
		raise Exception("Not implemented")

	def getNetProfit(self):
		"""Returns the difference between the order prices. **It does include commisions**."""
		if not self.getEntryOrder().isFilled():
			raise Exception("Position not opened yet")
		if self.getExitOrder() == None or not self.getExitOrder().isFilled():
			raise Exception("Position not closed yet")
		return self.getNetProfitImpl()

	def getNetProfitImpl(self):
		raise Exception("Not implemented")

	def buildExitOrder(self, price):
		raise Exception("Not implemented")

	def buildExitOnSessionCloseOrder(self):
		raise Exception("Not implemented")

# This class is reponsible for order management in long positions.
class LongPosition(Position):
	def __init__(self, broker_, instrument, price, quantity, goodTillCanceled):
		if price != None:
			entryOrder = broker.LimitOrder(broker.Order.Action.BUY, instrument, price, quantity, goodTillCanceled)
		else:
			entryOrder = broker.MarketOrder(broker.Order.Action.BUY, instrument, quantity, goodTillCanceled)
		Position.__init__(self, entryOrder)
		broker_.placeOrder(entryOrder)

	def getResultImpl(self):
		return utils.get_change_percentage(self.getExitOrder().getExecutionInfo().getPrice(), self.getEntryOrder().getExecutionInfo().getPrice())

	def getNetProfitImpl(self):
		ret = self.getExitOrder().getExecutionInfo().getPrice() - self.getEntryOrder().getExecutionInfo().getPrice()
		ret -= self.getEntryOrder().getExecutionInfo().getCommission()
		ret -= self.getExitOrder().getExecutionInfo().getCommission()
		return ret

	def buildExitOrder(self, price):
		if price:
			return broker.LimitOrder(broker.Order.Action.SELL, self.getInstrument(), price, self.getQuantity())
		else:
			return broker.MarketOrder(broker.Order.Action.SELL, self.getInstrument(), self.getQuantity())

	def buildExitOnSessionCloseOrder(self):
		return broker.MarketOrder(broker.Order.Action.SELL, self.getInstrument(), self.getQuantity(), useClosingPrice=True)

# This class is reponsible for order management in short positions.
class ShortPosition(Position):
	def __init__(self, broker_, instrument, price, quantity, goodTillCanceled):
		if price != None:
			entryOrder = broker.LimitOrder(broker.Order.Action.SELL_SHORT, instrument, price, quantity, goodTillCanceled)
		else:
			entryOrder = broker.MarketOrder(broker.Order.Action.SELL_SHORT, instrument, quantity, goodTillCanceled)
		Position.__init__(self, entryOrder)
		broker_.placeOrder(entryOrder)

	def getResultImpl(self):
		return utils.get_change_percentage(self.getEntryOrder().getExecutionInfo().getPrice(), self.getExitOrder().getExecutionInfo().getPrice())

	def getNetProfitImpl(self):
		ret = self.getEntryOrder().getExecutionInfo().getPrice() - self.getExitOrder().getExecutionInfo().getPrice()
		ret -= self.getEntryOrder().getExecutionInfo().getCommission()
		ret -= self.getExitOrder().getExecutionInfo().getCommission()
		return ret

	def buildExitOrder(self, price):
		if price:
			return broker.LimitOrder(broker.Order.Action.BUY, self.getInstrument(), price, self.getQuantity())
		else:
			return broker.MarketOrder(broker.Order.Action.BUY, self.getInstrument(), self.getQuantity())

	def buildExitOnSessionCloseOrder(self):
		return broker.MarketOrder(broker.Order.Action.BUY, self.getInstrument(), self.getQuantity(), useClosingPrice=True)

class Strategy:
	"""Base class for strategies. 

	:param barFeed: The bar feed to use to backtest the strategy.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
	:param cash: The amount of cash available.
	:type cash: int/float.

	.. note::
		This is a base class and should not be used directly.
	"""

	def __init__(self, barFeed, cash = 0):
		self.__feed = barFeed
		self.__broker = broker.Broker(cash)
		self.__broker.getOrderExecutedEvent().subscribe(self.__onOrderUpdate)
		self.__activePositions = {}
		self.__orderToPosition = {}
		self.__currentBars = None

	def __registerOrder(self, position, order):
		try:
			orders = self.__activePositions[position]
		except KeyError:
			orders = set()
			self.__activePositions[position] = orders

		if order.isAccepted():
			self.__orderToPosition[order] = position
			orders.add(order)

	def __unregisterOrder(self, position, order):
		del self.__orderToPosition[order]

		orders = self.__activePositions[position]
		orders.remove(order)
		if len(orders) == 0:
			del self.__activePositions[position]

	def __registerActivePosition(self, position):
		for order in [position.getEntryOrder(), position.getExitOrder()]:
			if order and order.isAccepted():
				self.__registerOrder(position, order)

	def getFeed(self):
		"""Returns the :class:`pyalgotrade.barfeed.BarFeed` that this strategy is using."""
		return self.__feed

	def getCurrentDateTime(self):
		"""Returns the :class:`datetime.datetime` for the current :class:`pyalgotrade.bar.Bar`."""
		ret = None
		if self.__currentBars:
			ret = self.__currentBars.getDateTime()
		return ret

	def getBroker(self):
		"""Returns the :class:`pyalgotrade.broker.Broker` used to handle order executions."""
		return self.__broker

	def enterLong(self, instrument, quantity, goodTillCanceled = False):
		"""Generates a buy market order to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry/exit orders are good till canceled. If False then orders get automatically canceled when session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`Position` entered.
		"""

		ret = LongPosition(self.__broker, instrument, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShort(self, instrument, quantity, goodTillCanceled = False):
		"""Generates a sell short market order to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry/exit orders are good till canceled. If False then orders get automatically canceled when session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`Position` entered.
		"""

		ret = ShortPosition(self.__broker, instrument, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterLongLimit(self, instrument, price, quantity, goodTillCanceled = False):
		"""Generates a buy limit order to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param price: Entry price.
		:type price: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry/exit orders are good till canceled. If False then orders get automatically canceled when session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`Position` entered.
		"""

		ret = LongPosition(self.__broker, instrument, price, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShortLimit(self, instrument, price, quantity, goodTillCanceled = False):
		"""Generates a sell short limit order to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param price: Entry price.
		:type price: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry/exit orders are good till canceled. If False then orders get automatically canceled when session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`Position` entered.
		"""

		ret = ShortPosition(self.__broker, instrument, price, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def exitPosition(self, position, price = None):
		"""Generates the exit order for the position.

		:param position: A position returned by :meth:`enterLong`, :meth:`enterShort`, :meth:`enterLongLimit` or :meth:`enterShortLimit` methods.
		:type position: :class:`Position`.
		:param price: Exit price. If set then a limit order is used instead of a market order.
		:type price: float.
		"""

		if	position.getExitOrder() != None and \
			(position.getExitOrder().isFilled() or position.getExitOrder().isAccepted()):
			# The position is already closed or the exit order execution is still pending.
			return

		# Before exiting a position, the entry order must have been filled.
		if position.getEntryOrder().isFilled():
			position.close(price, self.__broker)
			self.__registerActivePosition(position)
		else: # If the entry was not filled, cancel it.
			position.getEntryOrder().cancel()

	def onEnterOk(self, position):
		"""Override (optional) to get notified when the order submitted to enter a position was filled. The default implementation is empty.

		:param position: A position returned by :meth:`enterLong` or :meth:`enterShort`.
		:type position: :class:`Position`.
		"""
		pass

	def onEnterCanceled(self, position):
		"""Override (optional) to get notified when the order submitted to enter a position was canceled. The default implementation is empty.

		:param position: A position returned by :meth:`enterLong` or :meth:`enterShort`.
		:type position: :class:`Position`.
		"""
		pass

	# Called when the exit order for a position was filled.
	def onExitOk(self, position):
		"""Override (optional) to get notified when the order submitted to exit a position was filled. The default implementation is empty.

		:param position: A position returned by :meth:`enterLong` or :meth:`enterShort`.
		:type position: :class:`Position`.
		"""
		pass

	# Called when the exit order for a position was canceled.
	def onExitCanceled(self, position):
		"""Override (optional) to get notified when the order submitted to exit a position was canceled. The default implementation is empty.

		:param position: A position returned by :meth:`enterLong` or :meth:`enterShort`.
		:type position: :class:`Position`.
		"""
		pass

	"""Base class for strategies. """
	def onStart(self):
		"""Override (optional) to get notified when the strategy starts executing. The default implementation is empty. """
		pass

	def onFinish(self, bars):
		"""Override (optional) to get notified when the strategy finished executing. The default implementation is empty.

		:param bars: The latest bars processed.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		pass

	def onBars(self, bars):
		"""Override (mandatory) to get notified when new bars are available. The default implementation raises an Exception.

		**This is the method to override to enter your trading logic and enter/exit positions**.

		:param bars: The current bars.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		raise Exception("Not implemented")

	def __onOrderUpdate(self, order):
		position = self.__orderToPosition[order]
		if position.getEntryOrder() == order:
			if order.isFilled():
				self.onEnterOk(position)
			elif order.isCanceled():
				self.__unregisterOrder(position, order)
				self.onEnterCanceled(position)
			else:
				assert(False)
		elif position.getExitOrder() == order:
			if order.isFilled():
				self.__unregisterOrder(position, order)
				self.onExitOk(position)
			elif order.isCanceled():
				self.__unregisterOrder(position, order)
				self.onExitCanceled(position)
			else:
				assert(False)
		else:
			assert(False)

	def __checkExitOnSessionClose(self, bars):
		for position in self.__activePositions.keys():
			order = position.checkExitOnSessionClose(bars, self.getBroker())
			if order:
				self.__registerOrder(position, order)

	def __onBars(self, bars):
		# THE ORDER HERE IS VERY IMPORTANT
		self.__currentBars = bars

		# 1: Register exit-on-session-close orders if necessary.
		self.__checkExitOnSessionClose(bars)

		# 2: Let the broker process orders placed during previous call to onBars.
		# IT IS IMPORTANT TO EXECUTE THE BROKER FIRST TO AVOID EXECUTING ORDERS PLACED IN THE CURRENT TICK.
		self.getBroker().onBars(bars)

		# 3: Let the strategy process current bars and place orders.
		self.onBars(bars)

	def run(self):
		"""Call once (**and only once**) to backtest the strategy. """
		assert(self.__currentBars == None) # run should be called only once.
		try:
			self.__feed.getNewBarsEvent().subscribe(self.__onBars)
			self.onStart()
			self.__feed.processAll()
			if self.__currentBars != None:
				self.onFinish(self.__currentBars)
			else:
				raise Exception("Feed was empty")
		finally:
			self.__feed.getNewBarsEvent().unsubscribe(self.__onBars)

