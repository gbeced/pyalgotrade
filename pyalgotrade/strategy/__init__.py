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

import pyalgotrade.broker
import pyalgotrade.broker.backtesting
import pyalgotrade.observer
import pyalgotrade.strategy.position

class Strategy:
	"""Base class for strategies. 

	:param barFeed: The bar feed to use to backtest the strategy.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
	:param cash: The amount of cash available.
	:type cash: int/float.
	:param broker: Broker to use. If not specified the default backtesting broker (:class:`pyalgotrade.broker.backtesting.Broker`) 
					will be used.
	:type broker: :class:`pyalgotrade.broker.Broker`.

	.. note::
		This is a base class and should not be used directly.
	"""

	def __init__(self, barFeed, cash = 1000000, broker = None):
		self.__feed = barFeed
		self.__activePositions = set()
		self.__orderToPosition = {}
		self.__barsProcessedEvent = pyalgotrade.observer.Event()
		self.__analyzers = []
		self.__namedAnalyzers = {}

		if broker == None:
			# When doing backtesting (broker == None), the broker should subscribe to barFeed events before the strategy.
			# This is to avoid executing orders placed in the current tick.
			self.__broker = pyalgotrade.broker.backtesting.Broker(cash, barFeed)
		else:
			self.__broker = broker
		self.__broker.getOrderUpdatedEvent().subscribe(self.__onOrderUpdate)

	def getResult(self):
		return self.getBroker().getEquity()

	def getBarsProcessedEvent(self):
		return self.__barsProcessedEvent

	def __registerOrder(self, position, order):
		assert(position.isOpen()) # Why would be registering an order for a closed position ?
		self.__activePositions.add(position)
		assert(order.isAccepted())
		self.__orderToPosition[order] = position

	def __unregisterOrder(self, position, order):
		del self.__orderToPosition[order]
		if not position.isOpen():
			self.__activePositions.remove(position)

	def __registerActivePosition(self, position):
		for order in [position.getEntryOrder(), position.getExitOrder()]:
			if order and order.isAccepted():
				self.__registerOrder(position, order)

	def __notifyAnalyzers(self, lambdaExpression):
		for s in self.__analyzers:
			lambdaExpression(s)

	def attachAnalyzerEx(self, strategyAnalyzer, name = None):
		if strategyAnalyzer not in self.__analyzers:
			if name != None:
				if name in self.__namedAnalyzers:
					raise Exception("A different analyzer named '%s' was already attached" % name)
				self.__namedAnalyzers[name] = strategyAnalyzer

			strategyAnalyzer.beforeAttach(self)
			self.__analyzers.append(strategyAnalyzer)
			strategyAnalyzer.attached(self)

	def attachAnalyzer(self, strategyAnalyzer):
		"""Adds a :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`."""
		self.attachAnalyzerEx(strategyAnalyzer)

	def getNamedAnalyzer(self, name):
		return self.__namedAnalyzers.get(name, None)

	def getFeed(self):
		"""Returns the :class:`pyalgotrade.barfeed.BarFeed` that this strategy is using."""
		return self.__feed

	def getCurrentDateTime(self):
		"""Returns the :class:`datetime.datetime` for the current :class:`pyalgotrade.bar.Bar`."""
		ret = None
		bars = self.__feed.getCurrentBars()
		if bars:
			ret = bars.getDateTime()
		return ret

	def getBroker(self):
		"""Returns the :class:`pyalgotrade.broker.Broker` used to handle order executions."""
		return self.__broker

	def order(self, instrument, quantity, onClose = False, goodTillCanceled = False):
		"""Places a market order.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: The amount of shares. Positive means buy, negative means sell.
		:type quantity: int.
		:param onClose: True if the order should be filled as close to the closing price as possible (Market-On-Close order). Default is False.
		:type onClose: boolean.
		:param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.broker.MarketOrder` submitted.
		"""
		ret = None
		if quantity > 0:
			ret = self.getBroker().createMarketOrder(pyalgotrade.broker.Order.Action.BUY, instrument, quantity, onClose)
		elif quantity < 0:
			ret = self.getBroker().createMarketOrder(pyalgotrade.broker.Order.Action.SELL, instrument, abs(quantity), onClose)
		if ret:
			ret.setGoodTillCanceled(goodTillCanceled)
			self.getBroker().placeOrder(ret)
		return ret

	def enterLong(self, instrument, quantity, goodTillCanceled = False):
		"""Generates a buy :class:`pyalgotrade.broker.MarketOrder` to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.LongPosition(self, instrument, None, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShort(self, instrument, quantity, goodTillCanceled = False):
		"""Generates a sell short :class:`pyalgotrade.broker.MarketOrder` to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, None, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterLongLimit(self, instrument, limitPrice, quantity, goodTillCanceled = False):
		"""Generates a buy :class:`pyalgotrade.broker.LimitOrder` to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param limitPrice: Limit price.
		:type limitPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.LongPosition(self, instrument, limitPrice, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShortLimit(self, instrument, limitPrice, quantity, goodTillCanceled = False):
		"""Generates a sell short :class:`pyalgotrade.broker.LimitOrder` to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param limitPrice: Limit price.
		:type limitPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, limitPrice, None, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret
	
	def enterLongStop(self, instrument, stopPrice, quantity, goodTillCanceled = False):
		"""Generates a buy :class:`pyalgotrade.broker.StopOrder` to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param stopPrice: Stop price.
		:type stopPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.LongPosition(self, instrument, None, stopPrice, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShortStop(self, instrument, stopPrice, quantity, goodTillCanceled = False):
		"""Generates a sell short :class:`pyalgotrade.broker.StopOrder` to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param stopPrice: Stop price.
		:type stopPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, None, stopPrice, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterLongStopLimit(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled = False):
		"""Generates a buy :class:`pyalgotrade.broker.StopLimitOrder` order to enter a long position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param limitPrice: Limit price.
		:type limitPrice: float.
		:param stopPrice: Stop price.
		:type stopPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.LongPosition(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def enterShortStopLimit(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled = False):
		"""Generates a sell short :class:`pyalgotrade.broker.StopLimitOrder` order to enter a short position.

		:param instrument: Instrument identifier.
		:type instrument: string.
		:param limitPrice: Limit price.
		:type limitPrice: float.
		:param stopPrice: The Stop price.
		:type stopPrice: float.
		:param quantity: Entry order quantity.
		:type quantity: int.
		:param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
		:type goodTillCanceled: boolean.
		:rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
		"""

		ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled)
		self.__registerActivePosition(ret)
		return ret

	def exitPosition(self, position, limitPrice = None, stopPrice = None, goodTillCanceled = None):
		"""Generates the exit order for the position.

		:param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
		:type position: :class:`pyalgotrade.strategy.position.Position`.
		:param limitPrice: The limit price.
		:type limitPrice: float.
		:param stopPrice: The stop price.
		:type stopPrice: float.
		:param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
		:type goodTillCanceled: boolean.

		.. note::
			* If the entry order was not filled yet, it will be canceled.
			* If a previous exit order for this position was filled, this won't have any effect.
			* If a previous exit order for this position is pending, it will get canceled and the new exit order submitted.
			* If limitPrice is not set and stopPrice is not set, then a :class:`pyalgotrade.broker.MarketOrder` is used to exit the position.
			* If limitPrice is set and stopPrice is not set, then a :class:`pyalgotrade.broker.LimitOrder` is used to exit the position.
			* If limitPrice is not set and stopPrice is set, then a :class:`pyalgotrade.broker.StopOrder` is used to exit the position.
			* If limitPrice is set and stopPrice is set, then a :class:`pyalgotrade.broker.StopLimitOrder` is used to exit the position.
		"""

		if position.exitFilled():
			return

		# Before exiting a position, the entry order must have been filled.
		if position.getEntryOrder().isFilled():
			position.close(limitPrice, stopPrice, goodTillCanceled)
			self.__registerActivePosition(position)
		else: # If the entry was not filled, cancel it.
			self.getBroker().cancelOrder(position.getEntryOrder())

	def onEnterOk(self, position):
		"""Override (optional) to get notified when the order submitted to enter a position was filled. The default implementation is empty.

		:param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
		:type position: :class:`pyalgotrade.strategy.position.Position`.
		"""
		pass

	def onEnterCanceled(self, position):
		"""Override (optional) to get notified when the order submitted to enter a position was canceled. The default implementation is empty.

		:param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
		:type position: :class:`pyalgotrade.strategy.position.Position`.
		"""
		pass

	# Called when the exit order for a position was filled.
	def onExitOk(self, position):
		"""Override (optional) to get notified when the order submitted to exit a position was filled. The default implementation is empty.

		:param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
		:type position: :class:`pyalgotrade.strategy.position.Position`.
		"""
		pass

	# Called when the exit order for a position was canceled.
	def onExitCanceled(self, position):
		"""Override (optional) to get notified when the order submitted to exit a position was canceled. The default implementation is empty.

		:param position: A position returned by any of the enterLongXXX or enterShortXXX methods.
		:type position: :class:`pyalgotrade.strategy.position.Position`.
		"""
		pass

	"""Base class for strategies. """
	def onStart(self):
		"""Override (optional) to get notified when the strategy starts executing. The default implementation is empty. """
		pass

	def onFinish(self, bars):
		"""Override (optional) to get notified when the strategy finished executing. The default implementation is empty.

		:param bars: The last bars processed.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		pass

	def onBars(self, bars):
		"""Override (**mandatory**) to get notified when new bars are available. The default implementation raises an Exception.

		**This is the method to override to enter your trading logic and enter/exit positions**.

		:param bars: The current bars.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		raise NotImplementedError()

	def onOrderUpdated(self, order):
		"""Override (optional) to get notified when an order gets updated. This is only called if the order was placed using the broker interface directly.

		:param order: The order updated.
		:type order: :class:`pyalgotrade.broker.Order`.
		"""
		pass

	def __onOrderUpdate(self, broker, order):
		position = self.__orderToPosition.get(order, None)
		if position == None:
			self.onOrderUpdated(order)
		elif position.getEntryOrder() == order:
			if order.isFilled():
				self.__unregisterOrder(position, order)
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
			# The order used to belong to a position but it was ovewritten with a new one
			# and the previous order should have been canceled.
			assert(order.isCanceled())

	def __checkExitOnSessionClose(self, bars):
		for position in self.__activePositions:
			order = position.checkExitOnSessionClose(bars)
			if order:
				self.__registerOrder(position, order)

	def __onBars(self, bars):
		# THE ORDER HERE IS VERY IMPORTANT

		self.__notifyAnalyzers(lambda s: s.beforeOnBars(self))

		# 1: Let the strategy process current bars and place orders.
		self.onBars(bars)

		# 2: Place the necessary orders for positions marked to exit on session close.
		self.__checkExitOnSessionClose(bars)

		# 3: Notify that the bars were processed.
		self.__barsProcessedEvent.emit(self, bars)

	def run(self):
		"""Call once (**and only once**) to backtest the strategy. """
		try:
			self.__feed.getNewBarsEvent().subscribe(self.__onBars)
			self.__feed.start()
			self.__broker.start()
			self.onStart()

			# Dispatch events as long as the feed or the broker have something to dispatch.
			stopDispBroker = self.__broker.stopDispatching()
			stopDispFeed = self.__feed.stopDispatching()
			while not stopDispFeed or not stopDispBroker:
				if not stopDispBroker:
					self.__broker.dispatch()
				if not stopDispFeed:
					self.__feed.dispatch()
				stopDispBroker = self.__broker.stopDispatching()
				stopDispFeed = self.__feed.stopDispatching()

			if self.__feed.getCurrentBars() != None:
				self.onFinish(self.__feed.getCurrentBars())
			else:
				raise Exception("Feed was empty")
		finally:
			self.__feed.getNewBarsEvent().unsubscribe(self.__onBars)
			self.__broker.stop()
			self.__feed.stop()
			self.__broker.join()
			self.__feed.join()

