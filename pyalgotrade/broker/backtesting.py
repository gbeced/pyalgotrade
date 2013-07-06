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
from pyalgotrade import warninghelpers
import pyalgotrade.logger
import pyalgotrade.bar

logger = pyalgotrade.logger.getLogger("broker.backtesting")

######################################################################
## Commissions

class Commission:
	"""Base class for implementing different commission schemes.

	.. note::
		This is a base class and should not be used directly.
	"""

	def calculate(self, order, price, quantity):
		"""Calculates the commission for an order.

		:param order: The order being executed.
		:type order: :class:`pyalgotrade.broker.Order`.
		:param price: The price for each share.
		:type price: float.
		:param quantity: The order size.
		:type quantity: float.
		:rtype: float.
		"""
		raise NotImplementedError()

class NoCommission(Commission):
	"""A :class:`Commission` class that always returns 0."""

	def calculate(self, order, price, quantity):
		return 0

class FixedPerTrade(Commission):
	"""A :class:`Commission` class that charges a fixed amount for the whole trade.

	:param amount: The commission for an order.
	:type amount: float.
	"""
	def __init__(self, amount):
		self.__amount = amount

	def calculate(self, order, price, quantity):
		return self.__amount

class TradePercentage(Commission):
	"""A :class:`Commission` class that charges a percentage of the whole trade.

	:param percentage: The percentage to charge. 0.01 means 1%, and so on. It must be smaller than 1.
	:type percentage: float.
	"""
	def __init__(self, percentage):
		assert(percentage < 1)
		self.__percentage = percentage

	def calculate(self, order, price, quantity):
		return price * quantity * self.__percentage

######################################################################
## Order filling strategies

class FillStrategy:
	"""Base class for order filling strategies."""

	# Return the fill price for a MarketOrder or None.
	def fillMarketOrder(self, order, broker_, bar):
		"""Override to return the fill price for a market order or None if the order can't be filled at the given time.

		:param order: The order.
		:type order: :class:`pyalgotrade.broker.MarketOrder`.
		:param broker_: The broker.
		:type broker_: :class:`Broker`.
		:param bar: The current bar.
		:type bar: :class:`pyalgotrade.bar.Bar`.
		:rtype: An int/float with the fill price or None if the order should not be filled.
		"""
		raise NotImplementedError()

	# Return the fill price for a LimitOrder or None.
	def fillLimitOrder(self, order, broker_, bar):
		"""Override to return the fill price for a limit order or None if the order can't be filled at the given time.

		:param order: The order.
		:type order: :class:`pyalgotrade.broker.LimitOrder`.
		:param broker_: The broker.
		:type broker_: :class:`Broker`.
		:param bar: The current bar.
		:type bar: :class:`pyalgotrade.bar.Bar`.
		:rtype: An int/float with the fill price or None if the order should not be filled.
		"""
		raise NotImplementedError()

	# Return the fill price for a StopOrder or None.
	def fillStopOrder(self, order, broker_, bar):
		"""Override to return the fill price for a stop order or None if the order can't be filled at the given time.

		:param order: The order.
		:type order: :class:`pyalgotrade.broker.StopOrder`.
		:param broker_: The broker.
		:type broker_: :class:`Broker`.
		:param bar: The current bar.
		:type bar: :class:`pyalgotrade.bar.Bar`.
		:rtype: An int/float with the fill price or None if the order should not be filled.
		"""
		raise NotImplementedError()

	# Return the fill price for a StopLimitOrder or None.
	def fillStopLimitOrder(self, order, broker_, bar, justHitStopPrice):
		"""Override to return the fill price for a stop limit order or None if the order can't be filled at the given time.

		:param order: The order.
		:type order: :class:`pyalgotrade.broker.StopLimitOrder`.
		:param broker_: The broker.
		:type broker_: :class:`Broker`.
		:param bar: The current bar.
		:type bar: :class:`pyalgotrade.bar.Bar`.
		:param justHitStopPrice: True if the stop price has just been hit with the current bar.
		:type justHitStopPrice: boolean.
		:rtype: An int/float with the fill price or None if the order should not be filled.
		"""
		raise NotImplementedError()

class DefaultStrategy(FillStrategy):
	"""
	This strategy works as follows:

	* A :class:`pyalgotrade.broker.MarketOrder` is always filled using the open/close price.
	* A :class:`pyalgotrade.broker.LimitOrder` will be filled like this:
		* If the limit price was penetrated with the open price, then the open price is used.
		* If the bar includes the limit price, then the limit price is used.
		* Note that when buying the price is penetrated if it gets <= the limit price, and when selling the price is penetrated if it gets >= the limit price
	* A :class:`pyalgotrade.broker.StopOrder` will be filled like this:
		* If the stop price was penetrated with the open price, then the open price is used.
		* If the bar includes the stop price, then the stop price is used.
		* Note that when buying the price is penetrated if it gets >= the stop price, and when selling the price is penetrated if it gets <= the stop price
	* A :class:`pyalgotrade.broker.StopLimitOrder` will be filled like this:
		* If the stop price was penetrated with the open price, or if the bar includes the stop price, then the limit order becomes active.
		* If the limit order is active:
			* If the limit order was activated in this same bar and the limit price is penetrated as well, then the best between the stop price and the limit fill price (as described earlier) is used.
			* If the limit order was activated at a previous bar then the limit fill price (as described earlier) is used.

	.. note::
		This is the default strategy used by the Broker.
	"""
	def __getLimitOrderFillPrice(self, broker_, bar_, action, limitPrice):
		ret = None
		open_ = pyalgotrade.bar.get_open(bar_, broker_.getUseAdjustedValues())
		high = pyalgotrade.bar.get_high(bar_, broker_.getUseAdjustedValues())
		low = pyalgotrade.bar.get_low(bar_, broker_.getUseAdjustedValues())

		# If the bar is below the limit price, use the open price.
		# If the bar includes the limit price, use the open price or the limit price.
		if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			if high < limitPrice:
				ret = open_
			elif limitPrice >= low:
				if open_ < limitPrice: # The limit price was penetrated on open.
					ret = open_
				else:
					ret = limitPrice
		# If the bar is above the limit price, use the open price.
		# If the bar includes the limit price, use the open price or the limit price.
		elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			if low > limitPrice:
				ret = open_
			elif limitPrice <= high:
				if open_ > limitPrice: # The limit price was penetrated on open.
					ret = open_
				else:
					ret = limitPrice
		else: # Unknown action
			assert(False)
		return ret

	def fillMarketOrder(self, order, broker_, bar):
		if order.getFillOnClose():
			ret = pyalgotrade.bar.get_close(bar, broker_.getUseAdjustedValues())
		else:
			ret = pyalgotrade.bar.get_open(bar, broker_.getUseAdjustedValues())
		return ret

	# Return the fill price for a LimitOrder or None.
	def fillLimitOrder(self, order, broker_, bar):
		return self.__getLimitOrderFillPrice(broker_, bar, order.getAction(), order.getLimitPrice())

	# Return the fill price for a StopOrder or None.
	def fillStopOrder(self, order, broker_, bar):
		ret = None
		open_ = pyalgotrade.bar.get_open(bar, broker_.getUseAdjustedValues())
		high = pyalgotrade.bar.get_high(bar, broker_.getUseAdjustedValues())
		low = pyalgotrade.bar.get_low(bar, broker_.getUseAdjustedValues())
		stopPrice = order.getStopPrice()

		# If the bar is above the stop price, use the open price.
		# If the bar includes the stop price, use the open price or the stop price. Whichever is better.
		if order.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			if low > stopPrice:
				ret = open_
			elif stopPrice <= high:
				if open_ > stopPrice: # The stop price was penetrated on open.
					ret = open_
				else:
					ret = stopPrice
		# If the bar is below the stop price, use the open price.
		# If the bar includes the stop price, use the open price or the stop price. Whichever is better.
		elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			if high < stopPrice:
				ret = open_
			elif stopPrice >= low:
				if open_ < stopPrice: # The stop price was penetrated on open.
					ret = open_
				else:
					ret = stopPrice
		else: # Unknown action
			assert(False)
		return ret

	# Return the fill price for a StopLimitOrder or None.
	def fillStopLimitOrder(self, order, broker_, bar, justHitStopPrice):
		ret = self.__getLimitOrderFillPrice(broker_, bar, order.getAction(), order.getLimitPrice())
		# If we just hit the stop price, we need to make additional checks.
		if ret != None and justHitStopPrice:
			if order.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
				# If the stop price is lower than the limit price, then use that one. Else use the limit price.
				ret = min(order.getStopPrice(), order.getLimitPrice())
			elif order.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
				# If the stop price is greater than the limit price, then use that one. Else use the limit price.
				ret = max(order.getStopPrice(), order.getLimitPrice())
			else: # Unknown action
				assert(False)
		return ret

######################################################################
## Orders

class BacktestingOrder:
	def __init__(self):
		pass

	def checkCanceled(self, broker, bars):
		# This check is only for accepted orders that are not GTC.
		if self.getGoodTillCanceled() or not self.isAccepted():
			return

		# If its the last bar of the session and the order was not filled then cancel it.
		bar_ = bars.getBar(self.getInstrument())
		if bar_ != None and bar_.getSessionClose():
			broker.cancelOrder(self)

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			# Process the order if there is data available.
			bar_ = bars.getBar(self.getInstrument())
			if bar_ != None:
				self.tryExecuteImpl(broker, bar_)
			# Check if the order has to be canceled.
			self.checkCanceled(broker, bars)

class MarketOrder(broker.MarketOrder, BacktestingOrder):
	def __init__(self, orderId, action, instrument, quantity, onClose):
		broker.MarketOrder.__init__(self, orderId, action, instrument, quantity, onClose)
		BacktestingOrder.__init__(self)

	def tryExecuteImpl(self, broker_, bar_):
		price = broker_.getFillStrategy().fillMarketOrder(self, broker_, bar_)
		if price != None:
			broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

class LimitOrder(broker.LimitOrder, BacktestingOrder):
	def __init__(self, orderId, action, instrument, limitPrice, quantity):
		broker.LimitOrder.__init__(self, orderId, action, instrument, limitPrice, quantity)
		BacktestingOrder.__init__(self)

	def tryExecuteImpl(self, broker_, bar_):
		price = broker_.getFillStrategy().fillLimitOrder(self, broker_, bar_)
		if price != None:
			broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

class StopOrder(broker.StopOrder, BacktestingOrder):
	def __init__(self, orderId, action, instrument, stopPrice, quantity):
		broker.StopOrder.__init__(self, orderId, action, instrument, stopPrice, quantity)
		BacktestingOrder.__init__(self)

	def tryExecuteImpl(self, broker_, bar_):
		price = broker_.getFillStrategy().fillStopOrder(self, broker_, bar_)
		if price != None:
			broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(broker.StopLimitOrder, BacktestingOrder):
	def __init__(self, orderId, action, instrument, limitPrice, stopPrice, quantity):
		broker.StopLimitOrder.__init__(self, orderId, action, instrument, limitPrice, stopPrice, quantity)
		BacktestingOrder.__init__(self)

	def __stopHit(self, broker_, bar_):
		ret = False
		high = pyalgotrade.bar.get_high(bar_, broker_.getUseAdjustedValues())
		low = pyalgotrade.bar.get_low(bar_, broker_.getUseAdjustedValues())
		stopPrice = self.getStopPrice()

		# If the bar is above the stop price, or the bar includes the stop price, the stop was hit.
		if self.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			if low >= stopPrice or stopPrice <= high:
				ret = True
		# If the bar is below the stop price, or the bar includes the stop price, the stop was hit.
		elif self.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			if high <= stopPrice or stopPrice >= low:
				ret = True
		else: # Unknown action
			assert(False)
		return ret

	def tryExecuteImpl(self, broker_, bar_):
		justHitStopPrice = False

		# Check if we have to activate the limit order first.
		if not self.isLimitOrderActive() and self.__stopHit(broker_, bar_):
			self.setLimitOrderActive(True)
			justHitStopPrice = True

		# Check if we have ever reached the limit price
		if self.isLimitOrderActive():
			price = broker_.getFillStrategy().fillStopLimitOrder(self, broker_, bar_, justHitStopPrice)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

######################################################################
## Broker

class Broker(broker.Broker):
	"""Backtesting broker.

	:param cash: The initial amount of cash.
	:type cash: int/float.
	:param barFeed: The bar feed that will provide the bars.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
	:param commission: An object responsible for calculating order commissions.
	:type commission: :class:`Commission`
	"""

	def __init__(self, cash, barFeed, commission = None):
		broker.Broker.__init__(self)

		assert(cash >= 0)
		self.__cash = cash
		if commission is None:
			self.__commission = NoCommission()
		else:
			self.__commission = commission
		self.__shares = {}
		self.__activeOrders = {}
		self.__useAdjustedValues = False
		self.__fillStrategy = DefaultStrategy()

		# It is VERY important that the broker subscribes to barfeed events before the strategy.
		barFeed.getNewBarsEvent().subscribe(self.onBars)
		self.__barFeed = barFeed
		self.__allowNegativeCash = False
		self.__nextOrderId = 1

	def __getNextOrderId(self):
		ret = self.__nextOrderId
		self.__nextOrderId += 1
		return ret

	def __getBar(self, bars, instrument):
		ret = bars.getBar(instrument)
		if ret == None:
			ret = self.__barFeed.getLastBar(instrument)
		return ret

	def setAllowNegativeCash(self, allowNegativeCash):
		self.__allowNegativeCash = allowNegativeCash

	def getCash(self, includeShort = True):
		"""
		Returns the available cash.

		:param includeShort: Include cash from short positions.
		:type includeShort: boolean.
		"""
		ret = self.__cash
		if includeShort == False and self.__barFeed.getCurrentBars() != None:
			bars = self.__barFeed.getCurrentBars()
			for instrument, shares in self.__shares.iteritems():
				if shares < 0:
					instrumentPrice = pyalgotrade.bar.get_close(self.__getBar(bars, instrument), self.getUseAdjustedValues())
					ret += instrumentPrice * shares
		return ret

	def setCash(self, cash):
		"""Sets the available cash."""
		self.__cash = cash

	def getCommission(self):
		"""Returns the commission instance.

		:rtype: :class:`Commission`.
		"""
		return self.__commission

	def setCommission(self, commission):
		"""Sets the commission instance.

		:param commission: An object responsible for calculating order commissions.
		:type commission: :class:`Commission`.
		"""

		self.__commission = commission

	def setFillStrategy(self, strategy):
		"""Sets the :class:`FillStrategy` to use."""
		self.__fillStrategy = strategy 

	def getFillStrategy(self):
		"""Returns the :class:`FillStrategy` currently set."""
		return self.__fillStrategy

	def getUseAdjustedValues(self):
		return self.__useAdjustedValues

	def setUseAdjustedValues(self, useAdjusted):
		if not self.__barFeed.barsHaveAdjClose():
			raise Exception("The barfeed doesn't support adjusted close values")
		self.__useAdjustedValues = useAdjusted

	def getActiveOrders(self):
		return self.__activeOrders.values()

	def getPendingOrders(self):
		warninghelpers.deprecation_warning("getPendingOrders will be deprecated in the next version. Please use getActiveOrders instead.", stacklevel=2)
		return self.getActiveOrders()

	def getShares(self, instrument):
		self.__shares.setdefault(instrument, 0)
		return self.__shares[instrument]

	def getPositions(self):
		return self.__shares

	def getActiveInstruments(self):
		return [instrument for instrument, shares in self.__shares.iteritems() if shares != 0]

	def getEquityWithBars(self, bars):
		ret = self.getCash()
		if bars != None:
			for instrument, shares in self.__shares.iteritems():
				instrumentPrice = pyalgotrade.bar.get_close(self.__getBar(bars, instrument), self.getUseAdjustedValues())
				ret += instrumentPrice * shares
		return ret

	def getValue(self, deprecated = None):
		if deprecated != None:
			warninghelpers.deprecation_warning("The bars parameter is no longer used and will be removed in the next version.", stacklevel=2)

		return self.getEquityWithBars(self.__barFeed.getCurrentBars())

	def getEquity(self):
		"""Returns the portfolio value (cash + shares)."""
		return self.getEquityWithBars(self.__barFeed.getCurrentBars())

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
		else: # Unknown action
			assert(False)

		ret = False
		commission = self.getCommission().calculate(order, price, quantity)
		cost -= commission
		resultingCash = self.getCash() + cost

		# Check that we're ok on cash after the commission.
		if resultingCash >= 0 or self.__allowNegativeCash:
			# Commit the order execution.
			self.setCash(resultingCash)
			self.__shares[order.getInstrument()] = self.getShares(order.getInstrument()) + sharesDelta
			ret = True

			# Update the order.
			orderExecutionInfo = broker.OrderExecutionInfo(price, quantity, commission, dateTime)
			order.setExecuted(orderExecutionInfo)
		else:
			logger.debug("Not enough money to fill order %s" % (order))

		return ret

	def placeOrder(self, order):
		if order.isActive():
			if order.getId() not in self.__activeOrders:
				self.__activeOrders[order.getId()] = order
			# Switch from INITIAL -> SUBMITTED
			if order.getState() == broker.Order.State.INITIAL:
				order.setState(broker.Order.State.SUBMITTED)
		else:
			raise Exception("The order was already processed")

	def onBars(self, bars):
		for order in self.__activeOrders.values():
			# Switch from SUBMITTED -> ACCEPTED
			if order.isSubmitted():
				order.setState(broker.Order.State.ACCEPTED)
				self.getOrderUpdatedEvent().emit(self, order)

			if order.isAccepted():
				order.tryExecute(self, bars)
				if not order.isActive():
					del self.__activeOrders[order.getId()]
					self.getOrderUpdatedEvent().emit(self, order)
			else:
				assert(not order.isActive())
				del self.__activeOrders[order.getId()]
				self.getOrderUpdatedEvent().emit(self, order)

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

	def eof(self):
		# If there are no more events in the barfeed, then there is nothing left for us to do since all processing took
		# place while processing barfeed events.
		return self.__barFeed.eof()

	def dispatch(self):
		# All events were already emitted while handling barfeed events.
		pass
	
	def peekDateTime(self):
		return None

	def createMarketOrder(self, action, instrument, quantity, onClose = False):
		return MarketOrder(self.__getNextOrderId(), action, instrument, quantity, onClose)

	def createLimitOrder(self, action, instrument, limitPrice, quantity):
		return LimitOrder(self.__getNextOrderId(), action, instrument, limitPrice, quantity)

	def createStopOrder(self, action, instrument, stopPrice, quantity):
		return StopOrder(self.__getNextOrderId(), action, instrument, stopPrice, quantity)

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
		return StopLimitOrder(self.__getNextOrderId(), action, instrument, limitPrice, stopPrice, quantity)

	def cancelOrder(self, order):
		activeOrder = self.__activeOrders.get(order.getId())
		if activeOrder is None:
			raise Exception("The order is not active anymore")
		if activeOrder.isFilled():
			raise Exception("Can't cancel order that has already been filled")
		activeOrder.setState(broker.Order.State.CANCELED)

