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

from pyalgotrade import strategy
from pyalgotrade import barfeed
from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import ninjatraderfeed
import common
import time

import threading
import Queue

# This class decorates a barfeed.BarFeed and simulates an external barfeed that lives in a different thread.
class ExternalBarFeed(barfeed.BasicBarFeed):
	def __init__(self, decoratedBarFeed):
		barfeed.BasicBarFeed.__init__(self)
		self.__decorated = decoratedBarFeed
		self.__stopped = False

		# The barfeed runs in its own thread and will put bars in a queue that will be consumed by the strategy when fetchNextBars is called.
		self.__queue = Queue.Queue()

		# We're wrapping the barfeed so we need to register the same instruments.
		for instrument in decoratedBarFeed.getRegisteredInstruments():
			self.registerInstrument(instrument)

		# This is the thread that will run the barfeed.
		self.__thread = threading.Thread(target=self.__threadMain)

	def __threadMain(self):
		self.__decorated.start()

		# Just consume the bars and put them in a queue.
		bars = self.__decorated.getNextBars()
		while bars != None and not self.__stopped:
			self.__queue.put(bars)
			bars = self.__decorated.getNextBars()

		# Flag end of barfeed
		self.__queue.put(None)
		self.__decorated.stop()
		self.__decorated.join()

	def getNextBars(self):
		# Consume the bars from the queue.
		ret = None
		try:
			# If there is nothing there after 5 seconds, then treat this as the end.
			ret = self.__queue.get(True, 5)
		except Queue.Empty:
			ret = None
		return ret

	def start(self):
		self.__thread.start()

	def stop(self):
		self.__stopped = True

	def join(self):
		self.__thread.join()

class ExternalBroker(broker.BasicBroker):
	def __init__(self, cash, barFeed, commission=None):
		broker.BasicBroker.__init__(self, cash, commission)

		self.__ordersQueue = Queue.Queue()
		self.__stop = False

		# We're using a backtesting broker which only processes orders when bars are recevied.
		self.__decorated = backtesting.Broker(cash, barFeed, commission)
		# We'll queue events from the backtesting broker and forward those ONLY when dispatch is called.
		self.__decorated.getOrderUpdatedEvent().subscribe(self.__onOrderUpdated)

		self.__thread = threading.Thread(target=self.__threadMain)

	def __onOrderUpdated(self, broker_, order):
		self.__ordersQueue.put(order)

	def __threadMain(self):
		self.__decorated.start()

		# There is nothing special to do here since the backtesting broker will run when barfeed events are processed.
		while not self.__stop or not self.__ordersQueue.empty():
			time.sleep(1)

		self.__decorated.stop()
		self.__decorated.join()

	def setCash(self, cash):
		self.__decorated.setCash(cash)

	def getCash(self):
		return self.__decorated.getCash()

	def setUseAdjustedValues(self, useAdjusted):
		self.__decorated.setUseAdjustedValues(useAdjusted)

	def start(self):
		self.__thread.start()

	def stop(self):
		self.__stop = True

	def join(self):
		self.__thread.join()

	# Return True if there are not more events to dispatch.
	def stopDispatching(self):
		ret = self.__decorated.stopDispatching() and self.__ordersQueue.empty()
		return ret

	# Dispatch events.
	def dispatch(self):
		# Get orders from the queue and emit events.
		try:
			while True:
				order = self.__ordersQueue.get(False)
				self.getOrderUpdatedEvent().emit(self, order)
		except Queue.Empty:
			pass
	
	def placeOrder(self, order):
		return self.__decorated.placeOrder(order)
	
	def createMarketOrder(self, action, instrument, quantity, onClose, goodTillCanceled):
		return self.__decorated.createMarketOrder(action, instrument, quantity, onClose, goodTillCanceled)

	def createLimitOrder(self, action, instrument, limitPrice, quantity, goodTillCanceled):
		return self.__decorated.createLimitOrder(action, instrument, limitPrice, quantity, goodTillCanceled)

	def createStopOrder(self, action, instrument, stopPrice, quantity, goodTillCanceled):
		return self.__decorated.createStopOrder(action, instrument, stopPrice, quantity, goodTillCanceled)

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity, goodTillCanceled):
		return self.__decorated.createStopLimitOrder(action, instrument, stopPrice, limitPrice, quantity, goodTillCanceled)

	def createExecuteIfFilled(self, dependent, independent):
		return self.__decorated.createExecuteIfFilled(dependent, independent)

class StrategyTestCase(unittest.TestCase):
	TestInstrument = "doesntmatter"

	def __loadIntradayBarFeed(self, fromMonth=1, toMonth=1, fromDay=3, toDay=3):
		barFilter = csvfeed.USEquitiesRTH(datetime.datetime(2011, fromMonth, fromDay, 00, 00), datetime.datetime(2011, toMonth, toDay, 23, 55))
		barFeed = ninjatraderfeed.Feed(ninjatraderfeed.Frequency.MINUTE)
		barFeed.setBarFilter(barFilter)
		barFeed.addBarsFromCSV(StrategyTestCase.TestInstrument, common.get_data_file_path("nt-spy-minute-2011.csv"))
		return barFeed

	class TestStrategy(strategy.Strategy):
		def __init__(self, barFeed, cash, broker_ = None):
			strategy.Strategy.__init__(self, barFeed, cash, broker_)
			self.__longPositions = []
			self.__shortPositions = []

			self.__result = 0
			self.__netProfit = 0
			self.__enterOkEvents = 0
			self.__enterCanceledEvents = 0
			self.__exitOkEvents = 0
			self.__exitCanceledEvents = 0
			self.__gtc = False
			self.__exitOnSessionClose = False

		def setGoodTillCanceled(self, gtc):
			self.__gtc = gtc

		def setExitOnSessionClose(self, exitOnSessionClose):
			self.__exitOnSessionClose = exitOnSessionClose

		def addLongDatetimes(self, entryDateTime, exitDateTime):
			assert(entryDateTime != None)
			longPosInfo = [entryDateTime, exitDateTime, None]
			self.__longPositions.append(longPosInfo)

		def addShortDatetimes(self, entryDateTime, exitDateTime):
			assert(entryDateTime != None)
			shortPosInfo = [entryDateTime, exitDateTime, None]
			self.__shortPositions.append(shortPosInfo)
		
		def getEnterOkEvents(self):
			return self.__enterOkEvents

		def getExitOkEvents(self):
			return self.__exitOkEvents

		def getEnterCanceledEvents(self):
			return self.__enterCanceledEvents

		def getExitCanceledEvents(self):
			return self.__exitCanceledEvents

		def getResult(self):
			return self.__result

		def getNetProfit(self):
			return self.__netProfit

		def onStart(self):
			pass

		def onEnterOk(self, position):
			# print "Enter ok", position.getEntryOrder().getExecutionInfo().getDateTime()
			self.__enterOkEvents += 1

		def onEnterCanceled(self, position):
			# print "Enter canceled", position.getEntryOrder().getExecutionInfo().getDateTime()
			self.__enterCanceledEvents += 1

		def onExitOk(self, position):
			# print "Exit ok", position.getExitOrder().getExecutionInfo().getDateTime()
			self.__result += position.getResult()
			self.__netProfit += position.getNetProfit()
			self.__exitOkEvents += 1

		def onExitCanceled(self, position):
			# print "Exit canceled", position.getExitOrder().getExecutionInfo().getDateTime()
			self.__exitCanceledEvents += 1

		def onBars(self, bars):
			bar_ = bars.getBar(StrategyTestCase.TestInstrument)
			dateTime = bar_.getDateTime()

			# Check entry/exit for long positions.
			for posInfo in self.__longPositions:
				if posInfo[0] == dateTime:
					posInfo[2] = self.enterLong(StrategyTestCase.TestInstrument, 1, self.__gtc)
					posInfo[2].setExitOnSessionClose(self.__exitOnSessionClose)
				elif posInfo[1] == dateTime:
					assert(posInfo[2] != None) # Check that we actually entered the position.
					self.exitPosition(posInfo[2])

			# Check entry/exit for short positions.
			for posInfo in self.__shortPositions:
				if posInfo[0] == dateTime:
					posInfo[2] = self.enterShort(StrategyTestCase.TestInstrument, 1, self.__gtc)
					posInfo[2].setExitOnSessionClose(self.__exitOnSessionClose)
				elif posInfo[1] == dateTime:
					assert(posInfo[2] != None)
					self.exitPosition(posInfo[2])

		def onFinish(self, bars):
			pass

	def __createObjects(self, simulateExternalBarFeed = False, simulateExternalBroker = False):
		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV(StrategyTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		if simulateExternalBarFeed:
			barFeed = ExternalBarFeed(barFeed)

		broker_ = None
		if simulateExternalBroker:
			broker_ = ExternalBroker(1000, barFeed)

		strat = StrategyTestCase.TestStrategy(barFeed, 1000, broker_)
		return strat

	def __testLongPositionImpl(self, simulateExternalBarFeed, simulateExternalBroker):
		strat = self.__createObjects(simulateExternalBarFeed, simulateExternalBroker)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-11-08,27.37,27.50,24.50,24.81,63040000,24.26 - Sell
		# 2000-11-07,28.37,28.44,26.50,26.56,58950800,25.97 - Exit long
		# 2000-11-06,30.69,30.69,27.50,27.94,75552300,27.32 - Buy
		# 2000-11-03,31.50,31.75,29.50,30.31,65020900,29.64 - Enter long
		strat.addLongDatetimes(datetime.datetime(2000, 11, 3), datetime.datetime(2000, 11, 7))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 27.37 - 30.69, 2))
		self.assertTrue(round(strat.getResult(), 3) == -0.108)
		self.assertTrue(round(strat.getNetProfit(), 2) == round(27.37 - 30.69, 2))

	def testLongPosition(self):
		self.__testLongPositionImpl(False, False)

	def testLongPosition_ExternalBF(self):
		self.__testLongPositionImpl(True, False)

	def testLongPosition_ExternalBFAndBroker(self):
		self.__testLongPositionImpl(True, True)

	def __testShortPositionImpl(self, simulateExternalBarFeed, simulateExternalBroker):
		strat = self.__createObjects(simulateExternalBarFeed, simulateExternalBroker)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-11-08,27.37,27.50,24.50,24.81,63040000,24.26
		# 2000-11-07,28.37,28.44,26.50,26.56,58950800,25.97
		# 2000-11-06,30.69,30.69,27.50,27.94,75552300,27.32
		# 2000-11-03,31.50,31.75,29.50,30.31,65020900,29.64
		strat.addShortDatetimes(datetime.datetime(2000, 11, 3), datetime.datetime(2000, 11, 7))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 30.69 - 27.37, 2))
		self.assertTrue(round(strat.getResult(), 3) == 0.121)
		self.assertTrue(round(strat.getNetProfit(), 2) == round(30.69 - 27.37, 2))

	def testShortPosition(self):
		self.__testShortPositionImpl(False, False)

	def testShortPosition_ExternalBF(self):
		self.__testShortPositionImpl(True, False)

	def testShortPosition_ExternalBFAndBroker(self):
		self.__testShortPositionImpl(True, True)

	def __testLongPositionAdjCloseImpl(self, simulateExternalBarFeed, simulateExternalBroker):
		strat = self.__createObjects(simulateExternalBarFeed, simulateExternalBroker)
		strat.getBroker().setUseAdjustedValues(True)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-10-13,31.00,35.75,31.00,35.63,38516200,34.84
		# 2000-10-12,63.81,64.87,61.75,63.00,50892400,30.80
		# 2000-01-19,56.13,58.25,54.00,57.13,49208800,27.93
		# 2000-01-18,107.87,114.50,105.62,111.25,66791200,27.19
		strat.addLongDatetimes(datetime.datetime(2000, 1, 18), datetime.datetime(2000, 10, 12))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 30.31 - 27.44, 2))
		self.assertTrue(round(strat.getResult(), 3) == 0.105)
		self.assertTrue(round(strat.getNetProfit(), 2) == round(30.31 - 27.44, 2))

	def testLongPositionAdjClose(self):
		self.__testLongPositionAdjCloseImpl(False, False)

	def testLongPositionAdjClose_ExternalBF(self):
		self.__testLongPositionAdjCloseImpl(True, False)

	def testLongPositionAdjClose_ExternalBFAndBroker(self):
		self.__testLongPositionAdjCloseImpl(True, True)

	def __testShortPositionAdjCloseImpl(self, simulateExternalBarFeed, simulateExternalBroker):
		strat = self.__createObjects(simulateExternalBarFeed, simulateExternalBroker)
		strat.getBroker().setUseAdjustedValues(True)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-10-13,31.00,35.75,31.00,35.63,38516200,34.84
		# 2000-10-12,63.81,64.87,61.75,63.00,50892400,30.80
		# 2000-01-19,56.13,58.25,54.00,57.13,49208800,27.93
		# 2000-01-18,107.87,114.50,105.62,111.25,66791200,27.19
		strat.addShortDatetimes(datetime.datetime(2000, 1, 18), datetime.datetime(2000, 10, 12))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 27.44 - 30.31, 2))
		self.assertTrue(round(strat.getResult(), 3) == -0.095)
		self.assertTrue(round(strat.getNetProfit(), 2) == round(27.44 - 30.31, 2))

	def testShortPositionAdjClose(self):
		self.__testShortPositionAdjCloseImpl(False, False)

	def testShortPositionAdjClose_ExternalBF(self):
		self.__testShortPositionAdjCloseImpl(True, False)

	def testShortPositionAdjClose_ExternalBFAndBroker(self):
		self.__testShortPositionAdjCloseImpl(True, True)

	def __testShortPositionExitCanceledImpl(self, simulateExternalBarFeed, simulateExternalBroker):
		strat = self.__createObjects(simulateExternalBarFeed, simulateExternalBroker)
		strat.getBroker().setCash(0)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-12-08,30.06,30.62,29.25,30.06,40054100,29.39
		# 2000-12-07,29.62,29.94,28.12,28.31,41093000,27.68
		# .
		# 2000-11-29,23.19,23.62,21.81,22.87,75408100,22.36
		# 2000-11-28,23.50,23.81,22.25,22.66,43078300,22.16

		strat.addShortDatetimes(datetime.datetime(2000, 11, 28), datetime.datetime(2000, 12, 7))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitCanceledEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == 23.19)
		self.assertTrue(strat.getNetProfit() == 0)

	def testShortPositionExitCanceled(self):
		self.__testShortPositionExitCanceledImpl(False, False)

	def testShortPositionExitCanceled_ExternalBF(self):
		self.__testShortPositionExitCanceledImpl(True, False)

	def testShortPositionExitCanceled_ExternalBFAndBroker(self):
		self.__testShortPositionExitCanceledImpl(True, True)

	def testShortPositionExitCanceledAndReSubmitted(self):
		class TestStrategy(strategy.Strategy):
			def __init__(self, barFeed, cash):
				strategy.Strategy.__init__(self, barFeed, cash)
				self.__position = None
				self.__enterOkEvents = 0
				self.__enterCanceledEvents = 0
				self.__exitOkEvents = 0
				self.__exitCanceledEvents = 0

			def onStart(self):
				pass

			def onEnterOk(self, position):
				self.__enterOkEvents += 1

			def onEnterCanceled(self, position):
				self.__enterCanceledEvents += 1

			def onExitOk(self, position):
				self.__exitOkEvents += 1

			def onExitCanceled(self, position):
				self.__exitCanceledEvents += 1

			def getEnterOkEvents(self):
				return self.__enterOkEvents

			def getExitOkEvents(self):
				return self.__exitOkEvents

			def getEnterCanceledEvents(self):
				return self.__enterCanceledEvents

			def getExitCanceledEvents(self):
				return self.__exitCanceledEvents

			def onBars(self, bars):
				bar_ = bars.getBar(StrategyTestCase.TestInstrument)
				dateTime = bar_.getDateTime()
				if dateTime == datetime.datetime(2000, 11, 10):
					assert(self.__position == None)
					self.__position = self.enterShort(StrategyTestCase.TestInstrument, 1)
				elif dateTime == datetime.datetime(2000, 11, 14):
					assert(self.__position != None)
					# This should be canceled.
					self.exitPosition(self.__position)
				elif dateTime == datetime.datetime(2000, 11, 22):
					assert(self.__position != None)
					# This should be filled.
					self.exitPosition(self.__position)

		barFeed = yahoofeed.Feed()
		barFeed.addBarsFromCSV(StrategyTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
		strat = TestStrategy(barFeed, 0)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-11-24,23.31,24.25,23.12,24.12,22446100,23.58
		# 2000-11-22,23.62,24.06,22.06,22.31,53317000,21.81 - exitShort that gets filled
		# 2000-11-21,24.81,25.62,23.50,23.87,58651900,23.34
		# 2000-11-20,24.31,25.87,24.00,24.75,89783100,24.20
		# 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17
		# 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76
		# 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
		# 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74 - exitShort that gets canceled
		# 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20
		# 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterShort

		strat.run()
		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitCanceledEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(25.12 - 23.31, 2))

	def testLongPositionGTC(self):
		strat = self.__createObjects()
		strat.getBroker().setCash(48)
		strat.setGoodTillCanceled(True)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-02-07,59.31,60.00,58.42,59.94,44697200,29.30
		# 2000-02-04,57.63,58.25,56.81,57.81,40925000,28.26 - sell succeeds
		# 2000-02-03,55.38,57.00,54.25,56.69,55540600,27.71 - exit
		# 2000-02-02,54.94,56.00,54.00,54.31,63940400,26.55
		# 2000-02-01,51.25,54.31,50.00,54.00,57108800,26.40
		# 2000-01-31,47.94,50.13,47.06,49.95,68152400,24.42 - buy succeeds
		# 2000-01-28,51.50,51.94,46.63,47.38,86400600,23.16 - buy fails
		# 2000-01-27,55.81,56.69,50.00,51.81,61061800,25.33 - enterLong
		strat.addLongDatetimes(datetime.datetime(2000, 1, 27), datetime.datetime(2000, 2, 3))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(48 + 57.63 - 47.94, 2))
		self.assertTrue(round(strat.getNetProfit(), 2) == round(57.63 - 47.94, 2))

	def testExitOnCanceledEntry(self):
		strat = self.__createObjects()
		strat.getBroker().setCash(10)

		# Date,Open,High,Low,Close,Volume,Adj Close
		# 2000-02-07,59.31,60.00,58.42,59.94,44697200,29.30
		# 2000-02-04,57.63,58.25,56.81,57.81,40925000,28.26
		# 2000-02-03,55.38,57.00,54.25,56.69,55540600,27.71 - invalid exit since entry failed
		# 2000-02-02,54.94,56.00,54.00,54.31,63940400,26.55
		# 2000-02-01,51.25,54.31,50.00,54.00,57108800,26.40
		# 2000-01-31,47.94,50.13,47.06,49.95,68152400,24.42 - 
		# 2000-01-28,51.50,51.94,46.63,47.38,86400600,23.16 - buy fails
		# 2000-01-27,55.81,56.69,50.00,51.81,61061800,25.33 - enterLong
		strat.addLongDatetimes(datetime.datetime(2000, 1, 27), datetime.datetime(2000, 2, 3))

		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 0)
		self.assertTrue(strat.getEnterCanceledEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 0)
		self.assertTrue(strat.getExitCanceledEvents() == 0)
		self.assertTrue(strat.getBroker().getCash() == 10)
		self.assertTrue(strat.getNetProfit() == 0)

	def testIntradayExitOnClose(self):
		barFeed = self.__loadIntradayBarFeed()
		strat = StrategyTestCase.TestStrategy(barFeed, 1000)
		strat.setExitOnSessionClose(True)

		# 3/Jan/2011 18:20:00 - Short sell
		# 3/Jan/2011 18:21:00 - Sell at open price: 127.4
		# .
		# 3/Jan/2011 21:00:00 - Exit on close - Buy at close price: 127.05
		# The exit date should not be triggered
		strat.addShortDatetimes(datetime.datetime(2011, 1, 3, 18, 20), datetime.datetime(2011, 1, 4, 18, 20))
		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(strat.getEnterCanceledEvents() == 0)
		self.assertTrue(strat.getExitCanceledEvents() == 0)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.4 - 127.05), 2))
		self.assertTrue(round(strat.getNetProfit(), 2) == round(127.4 - 127.05, 2))

	def testIntradayExitOnClose_EntryNotFilled(self):
		# Test that if the entry gets canceled, then the exit on close order doesn't get submitted.
		barFeed = self.__loadIntradayBarFeed()
		strat = StrategyTestCase.TestStrategy(barFeed, 1)
		strat.setExitOnSessionClose(True)

		strat.addLongDatetimes(datetime.datetime(2011, 1, 3, 14, 30), None)
		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 0)
		self.assertTrue(strat.getExitOkEvents() == 0)
		self.assertTrue(strat.getEnterCanceledEvents() == 1)
		self.assertTrue(strat.getExitCanceledEvents() == 1)

	def testIntradayExitOnClose_AllInOneDay(self):
		barFeed = self.__loadIntradayBarFeed()
		strat = StrategyTestCase.TestStrategy(barFeed, 1000)
		strat.setExitOnSessionClose(True)

		# Enter on first bar, exit on close.
		strat.addLongDatetimes(datetime.datetime(2011, 1, 3, 14, 30), None)
		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(strat.getEnterCanceledEvents() == 0)
		self.assertTrue(strat.getExitCanceledEvents() == 0)

	def testIntradayExitOnClose_BuyOnLastBar(self):
		barFeed = self.__loadIntradayBarFeed()
		strat = StrategyTestCase.TestStrategy(barFeed, 1000)
		strat.setExitOnSessionClose(True)

		# 3/Jan/2011 20:59:00 - Enter long
		# 3/Jan/2011 21:00:00 - Buy at open price: 127.07 - Sell at close price: 127.05
		strat.addLongDatetimes(datetime.datetime(2011, 1, 3, 20, 59), datetime.datetime(2011, 1, 4, 18, 20))
		strat.run()

		self.assertTrue(strat.getEnterOkEvents() == 1)
		self.assertTrue(strat.getExitOkEvents() == 1)
		self.assertTrue(strat.getEnterCanceledEvents() == 0)
		self.assertTrue(strat.getExitCanceledEvents() == 0)
		self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (127.05 - 127.07), 2))
		self.assertTrue(round(strat.getNetProfit(), 2) == round(127.05 - 127.07, 2))

def getTestCases():
	ret = []
	ret.append(StrategyTestCase("testLongPosition"))
	ret.append(StrategyTestCase("testLongPosition_ExternalBF"))
	ret.append(StrategyTestCase("testLongPosition_ExternalBFAndBroker"))
	ret.append(StrategyTestCase("testShortPosition"))
	ret.append(StrategyTestCase("testShortPosition_ExternalBF"))
	ret.append(StrategyTestCase("testShortPosition_ExternalBFAndBroker"))
	ret.append(StrategyTestCase("testLongPositionAdjClose"))
	ret.append(StrategyTestCase("testLongPositionAdjClose_ExternalBF"))
	ret.append(StrategyTestCase("testLongPositionAdjClose_ExternalBFAndBroker"))
	ret.append(StrategyTestCase("testShortPositionAdjClose"))
	ret.append(StrategyTestCase("testShortPositionAdjClose_ExternalBF"))
	ret.append(StrategyTestCase("testShortPositionAdjClose_ExternalBFAndBroker"))
	ret.append(StrategyTestCase("testShortPositionExitCanceled"))
	ret.append(StrategyTestCase("testShortPositionExitCanceled_ExternalBF"))
	ret.append(StrategyTestCase("testShortPositionExitCanceled_ExternalBFAndBroker"))
	ret.append(StrategyTestCase("testShortPositionExitCanceledAndReSubmitted"))
	ret.append(StrategyTestCase("testLongPositionGTC"))
	ret.append(StrategyTestCase("testExitOnCanceledEntry"))
	ret.append(StrategyTestCase("testIntradayExitOnClose"))
	ret.append(StrategyTestCase("testIntradayExitOnClose_AllInOneDay"))
	ret.append(StrategyTestCase("testIntradayExitOnClose_EntryNotFilled"))
	ret.append(StrategyTestCase("testIntradayExitOnClose_BuyOnLastBar"))
	return ret

