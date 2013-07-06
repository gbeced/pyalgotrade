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

import unittest
import datetime

from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade import bar
from pyalgotrade import barfeed

class Callback:
	def __init__(self):
		self.eventCount = 0

	def onOrderUpdated(self, broker_, order):
		self.eventCount += 1

class BaseTestCase(unittest.TestCase):
	TestInstrument = "orcl"

	def setUp(self):
		self.__currMinutes = 0
		self.__nextDateTime = datetime.datetime(2011, 1, 2)

	def __getNextDateTime(self, switchDay):
		if switchDay:
			self.__nextDateTime = self.__nextDateTime + datetime.timedelta(days=1)
			self.__currMinutes = 0
		else:
			self.__currMinutes += 1
		return self.__nextDateTime + datetime.timedelta(minutes=self.__currMinutes)

	def buildBars(self, openPrice, highPrice, lowPrice, closePrice, sessionClose = False):
		ret = {}
		dateTime = self.__getNextDateTime(sessionClose)
		bar_ = bar.BasicBar(dateTime, openPrice, highPrice, lowPrice, closePrice, closePrice*10, closePrice)
		bar_.setSessionClose(sessionClose)
		ret[BaseTestCase.TestInstrument] = bar_
		return bar.Bars(ret)

class CommissionTestCase(unittest.TestCase):
	def testNoCommission(self):
		comm = backtesting.NoCommission()
		self.assertEqual(comm.calculate(None, 1, 1), 0)

	def testFixedPerTrade(self):
		comm = backtesting.FixedPerTrade(1.2)
		self.assertEqual(comm.calculate(None, 1, 1), 1.2)

	def testTradePercentage(self):
		comm = backtesting.TradePercentage(0.1)
		self.assertEqual(comm.calculate(None, 1, 1), 0.1)
		self.assertEqual(comm.calculate(None, 2, 2), 0.4)

class BrokerTestCase(BaseTestCase):
	def testRegressionGetActiveOrders(self):
		activeOrders = []

		def onOrderUpdated(broker, order):
			activeOrders.append(len(broker.getActiveOrders()))

		brk = backtesting.Broker(1000, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))
		brk.getOrderUpdatedEvent().subscribe(onOrderUpdated)
		brk.placeOrder(brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1))
		brk.placeOrder(brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1))
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertEqual(brk.getCash(), 1000 - 10*2)
		self.assertEqual(len(activeOrders), 4)
		self.assertEqual(activeOrders[0], 2) # First order gets accepted, both orders are active.
		self.assertEqual(activeOrders[1], 1) # First order gets filled, one order is active.
		self.assertEqual(activeOrders[2], 1) # Second order gets accepted, one order is active.
		self.assertEqual(activeOrders[3], 0) # Second order gets filled, zero orders are active.

class MarketOrderTestCase(BaseTestCase):
	def testBuyAndSell(self):
		brk = backtesting.Broker(11, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 1)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Sell
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 11)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testFailToBuy(self):
		brk = backtesting.Broker(5, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)

		# Fail to buy. No money.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

		# Fail to buy. No money. Canceled due to session close.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(11, 15, 8, 12, True))
		self.assertTrue(order.isCanceled())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testBuy_GTC(self):
		brk = backtesting.Broker(5, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		order.setGoodTillCanceled(True)

		# Fail to buy. No money.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		# Set sessionClose to true test that the order doesn't get canceled.
		brk.onBars(self.buildBars(10, 15, 8, 12, True))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(2, 15, 1, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 2)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 3)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)

	def testBuyAndSellInTwoSteps(self):
		brk = backtesting.Broker(20.4, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 0.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)

		# Sell
		order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 10.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)

		# Sell again
		order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(11, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(round(brk.getCash(), 1) == 21.4)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

	def testPortfolioValue(self):
		brk = backtesting.Broker(11, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 1)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)

		self.assertTrue(brk.getEquityWithBars(self.buildBars(11, 11, 11, 11)) == 11 + 1)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(1, 1, 1, 1)) == 1 + 1)

	def testBuyWithCommission(self):
		brk = backtesting.Broker(1020, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE), commission=backtesting.FixedPerTrade(10))

		# Buy
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 100)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 100)

	def testSellShort_1(self):
		brk = backtesting.Broker(1000, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Short sell
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(200, 200, 200, 200))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 1200)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(100, 100, 100, 100)) == 1000 + 100)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(0, 0, 0, 0)) == 1000 + 200)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(30, 30, 30, 30)) == 1000 + 170)

		# Buy at the same price.
		order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(200, 200, 200, 200))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 1000)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)

	def testSellShort_2(self):
		brk = backtesting.Broker(1000, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Short sell 1
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getCash() == 1100)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(100, 100, 100, 100)) == 1000)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(0, 0, 0, 0)) == 1000 + 100)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(70, 70, 70, 70)) == 1000 + 30)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(200, 200, 200, 200)) == 1000 - 100)

		# Buy 2 and earn 50
		order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(50, 50, 50, 50))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(brk.getCash() == 1000) # +50 from short sell operation, -50 from buy operation.
		self.assertTrue(brk.getEquityWithBars(self.buildBars(50, 50, 50, 50)) == 1000 + 50)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(70, 70, 70, 70)) == 1000 + 50 + 20)

		# Sell 1 and earn 50
		order = brk.createMarketOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(brk.getEquityWithBars(self.buildBars(70, 70, 70, 70)) == 1000 + 50 + 50)

	def testSellShort_3(self):
		brk = backtesting.Broker(100, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy 1
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(brk.getCash() == 0)

		# Sell 2
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 2)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(brk.getCash() == 200)

		# Buy 1
		order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(100, 100, 100, 100))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(brk.getCash() == 100)

	def testSellShortWithCommission(self):
		sharePrice = 100
		commission = 10
		brk = backtesting.Broker(1010, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE), commission=backtesting.FixedPerTrade(commission))

		# Sell 10 shares
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 10)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(sharePrice, sharePrice, sharePrice, sharePrice))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(brk.getCash() == 2000)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -10)

		# Buy the 10 shares sold short plus 9 extra
		order = brk.createMarketOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 19)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(sharePrice, sharePrice, sharePrice, sharePrice))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getCommission() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 9)
		self.assertTrue(brk.getCash() == sharePrice - commission)

	def testCancel(self):
		brk = backtesting.Broker(100, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.cancelOrder(order)
		brk.onBars(self.buildBars(10, 10, 10, 10))
		self.assertTrue(order.isCanceled())

	def testReSubmit(self):
		brk = backtesting.Broker(1000, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1, False)
		brk.placeOrder(order)
		order.setFillOnClose(True)
		brk.placeOrder(order) # Re-submit the order after changing it.
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 12)

class LimitOrderTestCase(BaseTestCase):
	def testBuyAndSell_HitTargetPrice(self):
		brk = backtesting.Broker(20, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 10, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(12, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Sell
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 17, 8, 10))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 15)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 25)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testBuyAndSell_GetBetterPrice(self):
		brk = backtesting.Broker(20, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 14, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(12, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 12)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 8)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Sell
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 15, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(16, 17, 8, 10))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 16)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 24)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testBuyAndSell_GappingBars(self):
		brk = backtesting.Broker(20, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Bar is below the target price.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 20, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 10))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Sell. Bar is above the target price.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 30, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(35, 40, 32, 35))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 35)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 45)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testFailToBuy(self):
		brk = backtesting.Broker(5, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 5, 1)

		# Fail to buy (couldn't get specific price).
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

		# Fail to buy (couldn't get specific price). Canceled due to session close.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(11, 15, 8, 12, True))
		self.assertTrue(order.isCanceled())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

	def testBuy_GTC(self):
		brk = backtesting.Broker(10, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 4, 2)
		order.setGoodTillCanceled(True)

		# Fail to buy (couldn't get specific price).
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)
		# Set sessionClose to true test that the order doesn't get canceled.
		brk.onBars(self.buildBars(10, 15, 8, 12, True))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(2, 15, 1, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 2)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 6)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
		self.assertTrue(cb.eventCount == 1)

	def testReSubmit(self):
		brk = backtesting.Broker(10, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		order = brk.createLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1, 1)
		order.setGoodTillCanceled(True)

		# Fail to buy (couldn't get specific price).
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.placeOrder(order)

		order.setLimitPrice(4)
		brk.placeOrder(order)

		order.setQuantity(2)
		brk.placeOrder(order)

		# Set sessionClose to true test that the order doesn't get canceled.
		brk.onBars(self.buildBars(10, 15, 8, 12, True))
		self.assertTrue(order.isAccepted())
		self.assertTrue(order.getExecutionInfo() == None)
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 1)

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		brk.onBars(self.buildBars(2, 15, 1, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 2)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 6)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 2)
		self.assertTrue(cb.eventCount == 1)

class StopOrderTestCase(BaseTestCase):
	def testLongPosStopLoss(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Create stop loss order.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 10, 12)) # Stop loss not hit.
		self.assertFalse(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)
		brk.onBars(self.buildBars(10, 15, 8, 12)) # Stop loss hit.
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 9)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5+9)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testLongPosStopLoss_GappingBars(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Create stop loss order.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 9, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 10, 12)) # Stop loss not hit.
		self.assertFalse(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)
		brk.onBars(self.buildBars(5, 8, 4, 7)) # Stop loss hit.
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 5)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5+5) # Fill the stop loss order at open price.
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testShortPosStopLoss(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Sell short
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 15+10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(cb.eventCount == 2)

		# Create stop loss order.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(8, 10, 7, 9)) # Stop loss not hit.
		self.assertFalse(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 15+10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(cb.eventCount == 1)
		brk.onBars(self.buildBars(10, 15, 8, 12)) # Stop loss hit.
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 15-1)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testShortPosStopLoss_GappingBars(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Sell short
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.SELL_SHORT, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 15+10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(cb.eventCount == 2)

		# Create stop loss order.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopOrder(broker.Order.Action.BUY_TO_COVER, BaseTestCase.TestInstrument, 11, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(8, 10, 7, 9)) # Stop loss not hit.
		self.assertFalse(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 15+10)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == -1)
		self.assertTrue(cb.eventCount == 1)
		brk.onBars(self.buildBars(15, 20, 13, 14)) # Stop loss hit.
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 15)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 15-5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

	def testReSubmit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createMarketOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, 1)
		brk.placeOrder(order)
		brk.onBars(self.buildBars(10, 15, 8, 12))
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)
		self.assertTrue(order.getExecutionInfo().getCommission() == 0)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 2)

		# Create stop loss order.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, 2, 1)
		brk.placeOrder(order)

		order.setStopPrice(9)
		brk.placeOrder(order)

		brk.onBars(self.buildBars(10, 15, 10, 12)) # Stop loss not hit.
		self.assertFalse(order.isFilled())
		self.assertTrue(len(brk.getActiveOrders()) == 1)
		self.assertTrue(brk.getCash() == 5)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 1)
		self.assertTrue(cb.eventCount == 1)
		brk.onBars(self.buildBars(10, 15, 8, 12)) # Stop loss hit.
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 9)
		self.assertTrue(len(brk.getActiveOrders()) == 0)
		self.assertTrue(brk.getCash() == 5+9)
		self.assertTrue(brk.getShares(BaseTestCase.TestInstrument) == 0)
		self.assertTrue(cb.eventCount == 2)

class StopLimitOrderTestCase(BaseTestCase):
	def testFillOpen(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 10. Buy <= 12.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(13, 15, 13, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit (bars include the price). Fill at open price.
		brk.onBars(self.buildBars(11, 15, 10, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)

		# Sell. Stop <= 8. Sell >= 6.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(4, 5, 3, 4))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit (bars include the price). Fill at open price.
		brk.onBars(self.buildBars(7, 8, 6, 7))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 7)

	def testFillOpen_GappingBars(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 10. Buy <= 12.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(13, 18, 13, 17))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit (bars don't include the price). Fill at open price.
		brk.onBars(self.buildBars(7, 9, 6, 8))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 7)

		# Sell. Stop <= 8. Sell >= 6.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(4, 5, 3, 4))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit (bars don't include the price). Fill at open price.
		brk.onBars(self.buildBars(10, 12, 8, 10))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)

	def testFillLimit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 10. Buy <= 12.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(13, 15, 13, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(13, 15, 10, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 12)

		# Sell. Stop <= 8. Sell >= 6.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(4, 5, 3, 4))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(5, 7, 5, 6))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 6)

	def testHitStopAndLimit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 10. Buy <= 12.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=10, limitPrice=12, quantity=1)
		brk.placeOrder(order)

		# Stop price hit. Limit price hit. Fill at stop price.
		brk.onBars(self.buildBars(9, 15, 8, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)

		# Sell. Stop <= 8. Sell >= 6.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=8, limitPrice=6, quantity=1)
		brk.placeOrder(order)

		# Stop price hit. Limit price hit. Fill at stop price.
		brk.onBars(self.buildBars(9, 10, 5, 8))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 8)

	def testInvertedPrices_FillOpen(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 12. Buy <= 10.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(11, 12, 10.5, 11))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at open price.
		brk.onBars(self.buildBars(9, 15, 8, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 9)

		# Sell. Stop <= 6. Sell >= 8.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(7, 7, 6, 7))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at open price.
		brk.onBars(self.buildBars(9, 10, 8, 9))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 9)

	def testInvertedPrices_FillOpen_GappingBars(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 12. Buy <= 10.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(11, 12, 10.5, 11))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at open price.
		brk.onBars(self.buildBars(7, 9, 6, 8))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 7)

		# Sell. Stop <= 6. Sell >= 8.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(7, 7, 6, 7))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at open price.
		brk.onBars(self.buildBars(10, 10, 9, 9))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)

	def testInvertedPrices_FillLimit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 12. Buy <= 10.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(11, 12, 10.5, 11))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(11, 13, 8, 9))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)

		# Sell. Stop <= 6. Sell >= 8.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(9, 10, 9, 10))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(7, 7, 6, 7))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(7, 10, 6, 9))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 8)

	def testInvertedPrices_HitStopAndLimit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 12. Buy <= 10.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=12, limitPrice=10, quantity=1)
		brk.placeOrder(order)

		# Stop price hit. Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(9, 15, 8, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 10)

		# Sell. Stop <= 6. Sell >= 8.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.SELL, BaseTestCase.TestInstrument, stopPrice=6, limitPrice=8, quantity=1)
		brk.placeOrder(order)

		# Stop price hit. Limit price hit. Fill at limit price.
		brk.onBars(self.buildBars(6, 10, 5, 7))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 8)

	def testReSubmit(self):
		brk = backtesting.Broker(15, barFeed=barfeed.BarFeed(barfeed.Frequency.MINUTE))

		# Buy. Stop >= 10. Buy <= 12.
		cb = Callback()
		brk.getOrderUpdatedEvent().subscribe(cb.onOrderUpdated)
		order = brk.createStopLimitOrder(broker.Order.Action.BUY, BaseTestCase.TestInstrument, stopPrice=1, limitPrice=1, quantity=1)
		brk.placeOrder(order)

		order.setLimitPrice(12)
		brk.placeOrder(order)

		order.setStopPrice(10)
		brk.placeOrder(order)

		# Stop price not hit. Limit price not hit.
		brk.onBars(self.buildBars(8, 9, 7, 8))
		self.assertFalse(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Stop price hit. Limit price not hit.
		brk.onBars(self.buildBars(13, 15, 13, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isAccepted())

		# Limit price hit (bars include the price). Fill at open price.
		brk.onBars(self.buildBars(11, 15, 10, 14))
		self.assertTrue(order.isLimitOrderActive())
		self.assertTrue(order.isFilled())
		self.assertTrue(order.getExecutionInfo().getPrice() == 11)

def getTestCases():
	ret = []

	ret.append(CommissionTestCase("testNoCommission"))
	ret.append(CommissionTestCase("testFixedPerTrade"))
	ret.append(CommissionTestCase("testTradePercentage"))

	ret.append(BrokerTestCase("testRegressionGetActiveOrders"))

	ret.append(MarketOrderTestCase("testBuyAndSell"))
	ret.append(MarketOrderTestCase("testFailToBuy"))
	ret.append(MarketOrderTestCase("testBuy_GTC"))
	ret.append(MarketOrderTestCase("testBuyAndSellInTwoSteps"))
	ret.append(MarketOrderTestCase("testPortfolioValue"))
	ret.append(MarketOrderTestCase("testBuyWithCommission"))
	ret.append(MarketOrderTestCase("testSellShort_1"))
	ret.append(MarketOrderTestCase("testSellShort_2"))
	ret.append(MarketOrderTestCase("testSellShort_3"))
	ret.append(MarketOrderTestCase("testSellShortWithCommission"))
	ret.append(MarketOrderTestCase("testCancel"))
	ret.append(MarketOrderTestCase("testReSubmit"))

	ret.append(LimitOrderTestCase("testBuyAndSell_HitTargetPrice"))
	ret.append(LimitOrderTestCase("testBuyAndSell_GetBetterPrice"))
	ret.append(LimitOrderTestCase("testBuyAndSell_GappingBars"))
	ret.append(LimitOrderTestCase("testFailToBuy"))
	ret.append(LimitOrderTestCase("testBuy_GTC"))
	ret.append(LimitOrderTestCase("testReSubmit"))

	ret.append(StopOrderTestCase("testLongPosStopLoss"))
	ret.append(StopOrderTestCase("testLongPosStopLoss_GappingBars"))
	ret.append(StopOrderTestCase("testShortPosStopLoss"))
	ret.append(StopOrderTestCase("testShortPosStopLoss_GappingBars"))
	ret.append(StopOrderTestCase("testReSubmit"))
	
	ret.append(StopLimitOrderTestCase("testFillOpen"))
	ret.append(StopLimitOrderTestCase("testFillOpen_GappingBars"))
	ret.append(StopLimitOrderTestCase("testFillLimit"))
	ret.append(StopLimitOrderTestCase("testHitStopAndLimit"))
	ret.append(StopLimitOrderTestCase("testInvertedPrices_FillOpen"))
	ret.append(StopLimitOrderTestCase("testInvertedPrices_FillOpen_GappingBars"))
	ret.append(StopLimitOrderTestCase("testInvertedPrices_FillLimit"))
	ret.append(StopLimitOrderTestCase("testInvertedPrices_HitStopAndLimit"))
	ret.append(StopLimitOrderTestCase("testReSubmit"))

	return ret

