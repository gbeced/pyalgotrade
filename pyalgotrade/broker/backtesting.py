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
## Filling strategies

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
		open_ = broker_.getBarOpen(bar_)
		high = broker_.getBarHigh(bar_)
		low = broker_.getBarLow(bar_)

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
			ret = broker_.getBarClose(bar)
		else:
			ret = broker_.getBarOpen(bar)
		return ret

	# Return the fill price for a LimitOrder or None.
	def fillLimitOrder(self, order, broker_, bar):
		return self.__getLimitOrderFillPrice(broker_, bar, order.getAction(), order.getLimitPrice())

	# Return the fill price for a StopOrder or None.
	def fillStopOrder(self, order, broker_, bar):
		ret = None
		open_ = broker_.getBarOpen(bar)
		high = broker_.getBarHigh(bar)
		low = broker_.getBarLow(bar)
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
	def checkCanceled(self, broker, bars):
		# If its the last bar of the session and the order is not GTC, then cancel it.
		if self.isAccepted() and self.getGoodTillCanceled() == False and bars.getBar(self.getInstrument()).getSessionClose():
			broker.cancelOrder(self)

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.tryExecuteImpl(broker, bars)
			self.checkCanceled(broker, bars)

class MarketOrder(broker.MarketOrder, BacktestingOrder):
	def __init__(self, action, instrument, quantity, onClose):
		broker.MarketOrder.__init__(self, action, instrument, quantity, onClose)

	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = broker_.getFillStrategy().fillMarketOrder(self, broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class LimitOrder(broker.LimitOrder, BacktestingOrder):
	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = broker_.getFillStrategy().fillLimitOrder(self, broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class StopOrder(broker.StopOrder, BacktestingOrder):
	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = broker_.getFillStrategy().fillStopOrder(self, broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(broker.StopLimitOrder, BacktestingOrder):
	def __stopHit(self, broker_, bar_):
		ret = False
		high = broker_.getBarHigh(bar_)
		low = broker_.getBarLow(bar_)
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

	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
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
		except KeyError:
			pass

######################################################################
## Broker

class Broker(broker.Broker):
	"""Backtesting broker.

	:param cash: The initial amount of cash.
	:type cash: int or float.
	:param barFeed: The bar feed that will provide the bars.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
	:param commission: An object responsible for calculating order commissions.
	:type commission: :class:`Commission`
	"""

	def __init__(self, cash, barFeed, commission = None):
		broker.Broker.__init__(self, cash, commission)
		self.__shares = {}
		self.__pendingOrders = []
		self.__useAdjustedValues = False
		self.__fillStrategy = DefaultStrategy()

		# It is VERY important that the broker subscribes to barfeed events before the strategy.
		barFeed.getNewBarsEvent().subscribe(self.onBars)
		self.__barFeed = barFeed

	def setFillStrategy(self, strategy):
		"""Sets the :class:`FillStrategy` to use."""
		self.__fillStrategy = strategy 

	def getFillStrategy(self):
		"""Returns the :class:`FillStrategy` currently set."""
		return self.__fillStrategy

	def getBarOpen(self, bar_):
		if self.getUseAdjustedValues():
			ret = bar_.getAdjOpen()
		else:
			ret = bar_.getOpen()
		return ret

	def getBarHigh(self, bar_):
		if self.getUseAdjustedValues():
			ret = bar_.getAdjHigh()
		else:
			ret = bar_.getHigh()
		return ret

	def getBarLow(self, bar_):
		if self.getUseAdjustedValues():
			ret = bar_.getAdjLow()
		else:
			ret = bar_.getLow()
		return ret

	def getBarClose(self, bar_):
		if self.getUseAdjustedValues():
			ret = bar_.getAdjClose()
		else:
			ret = bar_.getClose()
		return ret

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
		else: # Unknown action
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
		if order.isAccepted():
			if order not in self.__pendingOrders:
				self.__pendingOrders.append(order)
			order.setDirty(False)
		else:
			raise Exception("The order was already processed")

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
	
	def createMarketOrder(self, action, instrument, quantity, onClose = False):
		return MarketOrder(action, instrument, quantity, onClose)

	def createLimitOrder(self, action, instrument, limitPrice, quantity):
		return LimitOrder(action, instrument, limitPrice, quantity)

	def createStopOrder(self, action, instrument, stopPrice, quantity):
		return StopOrder(action, instrument, stopPrice, quantity)

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
		return StopLimitOrder(action, instrument, limitPrice, stopPrice, quantity)

	def cancelOrder(self, order):
		if order.isFilled():
			raise Exception("Can't cancel order that has already been filled")
		order.setState(broker.Order.State.CANCELED)

# vim: noet:ci:pi:sts=0:sw=4:ts=4
