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
	"""
	An :class:`Order` subclass that instructs the broker to buy or sell the stock immediately at the prevailing price, whatever that may be.
	If useClosingPrice is set to False then the opening price will be used to fill the order, otherwise the closing price will be used.
	"""
	def __init__(self, action, instrument, quantity, goodTillCanceled = False, useClosingPrice = False):
		price = 0
		broker.MarketOrder.__init__(self, action, instrument, quantity, goodTillCanceled)
		self.__useClosingPrice = useClosingPrice

	def __getPrice(self, broker, bar_):
		if self.__useClosingPrice:
			if broker.getUseAdjustedValues():
				ret = bar_.getAdjClose()
			else:
				ret = bar_.getClose()
		else:
			# Try to fill the order at the Open price.
			if broker.getUseAdjustedValues():
				ret = bar_.getAdjOpen()
			else:
				ret = bar_.getOpen()
		return ret

	def tryExecute(self, broker_, bars):
		try:
			if self.isAccepted():
				bar_ = bars.getBar(self.getInstrument())
				price = self.__getPrice(broker_, bar_)
				broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

				self.checkCanceled(bars)
		except KeyError:
			pass

class LimitOrder(broker.LimitOrder):
	"""
	An :class:`Order` subclass that instructs the broker to buy or sell the stock stock at a particular price.
	The purchase or sale will not happen unless you get your price.
	"""
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

	def tryExecute(self, broker_, bars):
		try:
			if self.isAccepted():
				bar_ = bars.getBar(self.getInstrument())
				price = self.__getPrice(broker_, bar_)
				if price:
					broker_.commitOrderExecution(self, price, self.getQuantity(), bar_.getDateTime())

				self.checkCanceled(bars)
		except KeyError:
			pass


class StopOrder(broker.StopOrder):
	"""
	An :class:`Order` subclass that gives your broker a price trigger that protects you from a big drop in a stock.
		You enter a stop loss order at a point below the current market price. If the stock falls to this price point, 
		the stop loss order becomes a market order and your broker sells the stock. If the stock stays level or rises, 
		the stop loss order does nothing.
	"""
	def tryExecute(self, broker_, bars):
		try:
			if self.isAccepted():
				bar_ = bars.getBar(self.getInstrument())

				# Check if we have reached the limit price:
				high = bar_.getHigh()
				low = bar_.getLow()

				stopPrice = self.getPrice()
				action = self.getAction()

				# Stop price reached, initiate a market order.
				# Fill the market order with the worst price: 
				#	High for Long, Low for Short orders
				if stopPrice <= high and action == broker.Order.Action.BUY:
					orderPrice = high
					broker_.commitOrderExecution(self, orderPrice, self.getQuantity(), bar_.getDateTime())
				elif stopPrice >= low and action in (broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT):
					orderPrice = low
					broker_.commitOrderExecution(self, orderPrice, self.getQuantity(), bar_.getDateTime())

				self.checkCanceled(bars)
		except KeyError:
			pass


class StopLimitOrder(broker.StopLimitOrder):
	"""
	An :class:`Order` subclass that gives your broker a price trigger that protects you from a big drop in a stock.
		You enter a stop loss order at a point below the current market price. If the stock falls to this price point, 
		the stop loss order becomes a limit order with the defined limit price. If the stock stays level or rises, 
		the stop loss order does nothing.
	"""
	def tryExecute(self, broker_, bars):
		try:
			if self.isAccepted():
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

				self.checkCanceled(bars)
		except KeyError:
			pass



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
		if order.getAction() == broker.Order.Action.BUY:
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
	
	def createLongMarketOrder(self, instrument, quantity, goodTillCanceled=False, useClosingPrice=False): 
		return(MarketOrder(broker.Order.Action.BUY, instrument, quantity, goodTillCanceled, useClosingPrice))

	def createShortMarketOrder(self, instrument, quantity, goodTillCanceled=False, useClosingPrice=False): 
		return(MarketOrder(broker.Order.Action.SELL, instrument, quantity, goodTillCanceled, useClosingPrice))

	def createLongLimitOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		return(LimitOrder(broker.Order.Action.BUY, instrument, price, quantity, goodTillCanceled))

	def createShortLimitOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		return(LimitOrder(broker.Order.Action.SELL, instrument, price, quantity, goodTillCanceled))

	def createLongStopOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		return(StopOrder(broker.Order.Action.BUY, instrument, price, quantity, goodTillCanceled))

	def createShortStopOrder(self, instrument, price, quantity, goodTillCanceled=False): 
		return(StopOrder(broker.Order.Action.SELL, instrument, price, quantity, goodTillCanceled))

	def createLongStopLimitOrder(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False): 
		return(StopLimitOrder(broker.Order.Action.BUY, instrument, limitPrice, stopPrice, quantity, goodTillCanceled))

	def createShortStopLimitOrder(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False): 
		return(StopLimitOrder(broker.Order.Action.SELL, instrument, limitPrice, stopPrice, quantity, goodTillCanceled))

# vim: noet:ci:pi:sts=0:sw=4:ts=4
