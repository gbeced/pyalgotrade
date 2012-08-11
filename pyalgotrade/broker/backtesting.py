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

class BacktestingOrder:
	def checkCanceled(self, bars):
		# If its the last bar of the session and the order is not GTC, then cancel it.
		if self.isAccepted() and self.getGoodTillCanceled() == False and bars.getBar(self.getInstrument()).getSessionClose():
			self.cancel()

	def tryExecute(self, broker, bars):
		if self.isAccepted():
			self.tryExecuteImpl(broker, bars)
			self.checkCanceled(bars)

class MarketOrder(broker.MarketOrder, BacktestingOrder):
	def __init__(self, action, instrument, quantity, onClose, goodTillCanceled):
		broker.MarketOrder.__init__(self, action, instrument, quantity, goodTillCanceled)
		self.__onClose = onClose

	def __getFillPrice(self, broker_, bar_):
		# Fill the order at the open or close price (as in NinjaTrader).
		if self.__onClose:
			ret = broker_.getBarClose(bar_)
		else:
			ret = broker_.getBarOpen(bar_)
		return ret

	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getFillPrice(broker_, bar_)
			broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

# Returns the fill price for a limit order or None. 
def get_limit_order_fill_price(broker_, bar_, action, limitPrice):
	ret = None
	open_ = broker_.getBarOpen(bar_)
	high = broker_.getBarHigh(bar_)
	low = broker_.getBarLow(bar_)

	# If the bar is below the limit price, use the open price.
	# If the bar includes the limit price, use the open price or the limit price. Whichever is better.
	if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
		if high < limitPrice:
			ret = open_
		elif limitPrice >= low:
			if open_ < limitPrice: # The limit price was penetrated on open.
				ret = open_
			else:
				ret = limitPrice
	# If the bar is above the limit price, use the open price.
	# If the bar includes the limit price, use the open price or the limit price. Whichever is better.
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

class LimitOrder(broker.LimitOrder, BacktestingOrder):
	def __getFillPrice(self, broker_, bar_):
		return get_limit_order_fill_price(broker_, bar_, self.getAction(), self.getPrice())

	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getFillPrice(broker_, bar_)
			if price != None:
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
		except KeyError:
			pass

class StopOrder(broker.StopOrder, BacktestingOrder):
	def __getFillPrice(self, broker_, bar_):
		ret = None
		open_ = broker_.getBarOpen(bar_)
		high = broker_.getBarHigh(bar_)
		low = broker_.getBarLow(bar_)
		stopPrice = self.getPrice()

		# If the bar is above the stop price, use the open price.
		# If the bar includes the stop price, use the open price or the stop price. Whichever is better.
		if self.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
			if low > stopPrice:
				ret = open_
			elif stopPrice <= high:
				if open_ > stopPrice: # The stop price was penetrated on open.
					ret = open_
				else:
					ret = stopPrice
		# If the bar is below the stop price, use the open price.
		# If the bar includes the stop price, use the open price or the stop price. Whichever is better.
		elif self.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
			if high < stopPrice:
				ret = open_
			if stopPrice >= low:
				if open_ < stopPrice: # The stop price was penetrated on open.
					ret = open_
				else:
					ret = stopPrice
		else: # Unknown action
			assert(False)
		return ret

	def tryExecuteImpl(self, broker_, bars):
		try:
			bar_ = bars.getBar(self.getInstrument())
			price = self.__getFillPrice(broker_, bar_)
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

	def __getFillPrice(self, broker_, bar_, justHitStopPrice):
		ret = get_limit_order_fill_price(broker_, bar_, self.getAction(), self.getPrice())
		# If we just hit the stop price, we need to make additional checks.
		if ret != None and justHitStopPrice:
			if self.getAction() in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
				# If the stop price is lower than the limit price, then use that one. Else use the limit price.
				ret = min(self.getStopPrice(), self.getPrice())
			elif self.getAction() in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
				# If the stop price is greater than the limit price, then use that one. Else use the limit price.
				ret = max(self.getStopPrice(), self.getPrice())
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
				price = self.__getFillPrice(broker_, bar_, justHitStopPrice)
				if price != None:
					broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())
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

	def createLimitOrder(self, action, instrument, limitPrice, quantity, goodTillCanceled):
		return LimitOrder(action, instrument, limitPrice, quantity, goodTillCanceled)

	def createStopOrder(self, action, instrument, stopPrice, quantity, goodTillCanceled):
		return StopOrder(action, instrument, stopPrice, quantity, goodTillCanceled)

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity, goodTillCanceled):
		return StopLimitOrder(action, instrument, limitPrice, stopPrice, quantity, goodTillCanceled)

	def createExecuteIfFilled(self, dependent, independent):
		return ExecuteIfFilled(dependent, independent)

# vim: noet:ci:pi:sts=0:sw=4:ts=4
