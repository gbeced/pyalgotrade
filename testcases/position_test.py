# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import datetime
import pytz

import common
import strategy_test

from pyalgotrade import bar
from pyalgotrade import strategy
from pyalgotrade.strategy import position
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import barfeed
from pyalgotrade.barfeed import membf
from pyalgotrade.barfeed import ninjatraderfeed
from pyalgotrade.utils import dt
from pyalgotrade import marketsession


def load_daily_barfeed(instrument):
    barFeed = yahoofeed.Feed()
    barFeed.addBarsFromCSV(instrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
    return barFeed


def us_equities_datetime(*args, **kwargs):
    ret = datetime.datetime(*args, **kwargs)
    ret = dt.localize(ret, marketsession.USEquities.getTimezone())
    return ret


class TestBarFeed(membf.BarFeed):
    def barsHaveAdjClose(self):
        raise NotImplementedError()


class BaseTestStrategy(strategy.BacktestingStrategy):
    def __init__(self, barFeed, instrument, cash=1000000):
        strategy.BacktestingStrategy.__init__(self, barFeed, cash)
        self.instrument = instrument
        self.orderUpdatedCalls = 0
        self.enterOkCalls = 0
        self.enterCanceledCalls = 0
        self.exitOkCalls = 0
        self.exitCanceledCalls = 0
        self.posExecutionInfo = []

    def onOrderUpdated(self, order):
        self.orderUpdatedCalls += 1

    def onEnterOk(self, position):
        self.enterOkCalls += 1
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onEnterCanceled(self, position):
        self.enterCanceledCalls += 1
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onExitOk(self, position):
        self.exitOkCalls += 1
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())

    def onExitCanceled(self, position):
        self.exitCanceledCalls += 1
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())


class TestStrategy(BaseTestStrategy):
    def __init__(self, barFeed, instrument, cash):
        BaseTestStrategy.__init__(self, barFeed, instrument, cash)

        self.__activePosition = None
        # Maps dates to a tuple of (method, params)
        self.__posEntry = {}
        self.__posExit = {}

        self.__result = 0
        self.__netProfit = 0
        self.positions = []

    def addPosEntry(self, dateTime, enterMethod, *args, **kwargs):
        self.__posEntry.setdefault(dateTime, [])
        self.__posEntry[dateTime].append((enterMethod, args, kwargs))

    def addPosExitMarket(self, dateTime, *args, **kwargs):
        self.__posExit.setdefault(dateTime, [])
        self.__posExit[dateTime].append((position.Position.exitMarket, args, kwargs))

    def addPosExitLimit(self, dateTime, *args, **kwargs):
        self.__posExit.setdefault(dateTime, [])
        self.__posExit[dateTime].append((position.Position.exitLimit, args, kwargs))

    def addPosExitStop(self, dateTime, *args, **kwargs):
        self.__posExit.setdefault(dateTime, [])
        self.__posExit[dateTime].append((position.Position.exitStop, args, kwargs))

    def addPosExitStopLimit(self, dateTime, *args, **kwargs):
        self.__posExit.setdefault(dateTime, [])
        self.__posExit[dateTime].append((position.Position.exitStopLimit, args, kwargs))

    def getResult(self):
        return self.__result

    def getNetProfit(self):
        return self.__netProfit

    def getActivePosition(self):
        return self.__activePosition

    def onEnterOk(self, position):
        # print "Enter ok", position.getEntryOrder().getExecutionInfo().getDateTime()
        BaseTestStrategy.onEnterOk(self, position)
        if self.__activePosition is None:
            self.__activePosition = position
            assert(position.isOpen())
            assert(len(position.getActiveOrders()) != 0)
            assert(position.getShares() != 0)

    def onEnterCanceled(self, position):
        # print "Enter canceled", position.getEntryOrder().getExecutionInfo().getDateTime()
        BaseTestStrategy.onEnterCanceled(self, position)
        self.__activePosition = None
        assert(not position.isOpen())
        assert(len(position.getActiveOrders()) == 0)
        assert(position.getShares() == 0)

    def onExitOk(self, position):
        # print "Exit ok", position.getExitOrder().getExecutionInfo().getDateTime()
        BaseTestStrategy.onExitOk(self, position)
        self.__result += position.getReturn()
        self.__netProfit += position.getPnL()
        self.__activePosition = None
        assert(not position.isOpen())
        assert(len(position.getActiveOrders()) == 0)
        assert(position.getShares() == 0)

    def onExitCanceled(self, position):
        # print "Exit canceled", position.getExitOrder().getExecutionInfo().getDateTime()
        BaseTestStrategy.onExitCanceled(self, position)
        assert(position.isOpen())
        assert(len(position.getActiveOrders()) == 0)
        assert(position.getShares() != 0)

    def onBars(self, bars):
        dateTime = bars.getDateTime()

        # Check position entry.
        for meth, args, kwargs in strategy_test.get_by_datetime_or_date(self.__posEntry, dateTime):
            if self.__activePosition is not None:
                raise Exception("Only one position allowed at a time")
            self.__activePosition = meth(*args, **kwargs)
            self.positions.append(self.__activePosition)

        # Check position exit.
        for meth, args, kwargs in strategy_test.get_by_datetime_or_date(self.__posExit, dateTime):
            if self.__activePosition is None:
                raise Exception("A position was not entered")
            meth(self.__activePosition, *args, **kwargs)


class EnterAndExitStrategy(BaseTestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif self.position.entryFilled() and not self.position.exitFilled():
            self.position.exitMarket()


class DoubleExitStrategy(BaseTestStrategy):
    def onStart(self):
        self.position = None
        self.doubleExit = False
        self.doubleExitFailed = False

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif not self.doubleExit:
            self.doubleExit = True
            self.position.exitMarket()
            try:
                self.position.exitMarket()
            except Exception:
                self.doubleExitFailed = True


class CancelEntryStrategy(BaseTestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
            self.position.cancelEntry()


class ExitEntryNotFilledStrategy(BaseTestStrategy):
    def onStart(self):
        self.position = None

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
            self.position.exitMarket()


class ResubmitExitStrategy(BaseTestStrategy):
    def onStart(self):
        self.position = None
        self.exitRequestCanceled = False

    def onBars(self, bars):
        if self.position is None:
            self.position = self.enterLong(self.instrument, 1)
        elif self.position.entryFilled() and not self.position.exitFilled():
            self.position.exitMarket()
            if not self.exitRequestCanceled:
                self.position.cancelExit()
                self.exitRequestCanceled = True


class BaseTestCase(common.TestCase):
    TestInstrument = "doesntmatter"

    def loadIntradayBarFeed(self):
        fromMonth = 1
        toMonth = 1
        fromDay = 3
        toDay = 3
        barFilter = csvfeed.USEquitiesRTH(us_equities_datetime(2011, fromMonth, fromDay, 00, 00), us_equities_datetime(2011, toMonth, toDay, 23, 59))
        barFeed = ninjatraderfeed.Feed(barfeed.Frequency.MINUTE)
        barFeed.setBarFilter(barFilter)
        barFeed.addBarsFromCSV(BaseTestCase.TestInstrument, common.get_data_file_path("nt-spy-minute-2011.csv"))
        return barFeed

    def loadDailyBarFeed(self):
        barFeed = yahoofeed.Feed()
        barFeed.addBarsFromCSV(BaseTestCase.TestInstrument, common.get_data_file_path("orcl-2000-yahoofinance.csv"))
        return barFeed

    def createStrategy(self, useIntradayBarFeed=False):
        if useIntradayBarFeed:
            barFeed = self.loadIntradayBarFeed()
        else:
            barFeed = self.loadDailyBarFeed()

        strat = TestStrategy(barFeed, BaseTestCase.TestInstrument, 1000)
        return strat


class LongPosTestCase(BaseTestCase):
    def testEnterAndExit(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = EnterAndExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.position.isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)
        self.assertEqual(strat.orderUpdatedCalls, 4)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)
        self.assertEqual(strat.position.getAge().days, 1)

    def testCancelEntry(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = CancelEntryStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.position.isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.exitCanceledCalls, 0)
        self.assertEqual(strat.orderUpdatedCalls, 1)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)
        self.assertEqual(strat.position.getAge().total_seconds(), 0)

    def testExitEntryNotFilled(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = ExitEntryNotFilledStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.position.isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.exitCanceledCalls, 0)
        self.assertEqual(strat.orderUpdatedCalls, 1)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)
        self.assertEqual(strat.position.getAge().total_seconds(), 0)

    def testDoubleExitFails(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = DoubleExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.position.isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)
        self.assertEqual(strat.orderUpdatedCalls, 4)
        self.assertEqual(strat.doubleExit, True)
        self.assertEqual(strat.doubleExitFailed, True)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)
        self.assertEqual(strat.position.getAge().days, 1)

    def testResubmitExit(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = ResubmitExitStrategy(barFeed, instrument)
        strat.run()

        self.assertEqual(strat.position.isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 1)
        self.assertEqual(strat.orderUpdatedCalls, 5)
        self.assertEqual(len(strat.getActivePositions()), 0)
        self.assertEqual(len(strat.getOrderToPosition()), 0)
        self.assertEqual(strat.position.getAge().days, 2)

    def testLongPosition(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-08,27.37,27.50,24.50,24.81,63040000,24.26 - Sell
        # 2000-11-07,28.37,28.44,26.50,26.56,58950800,25.97 - Exit long
        # 2000-11-06,30.69,30.69,27.50,27.94,75552300,27.32 - Buy
        # 2000-11-03,31.50,31.75,29.50,30.31,65020900,29.64 - Enter long

        strat.addPosEntry(datetime.datetime(2000, 11, 3), strat.enterLong, BaseTestCase.TestInstrument, 1, False)
        strat.addPosExitMarket(datetime.datetime(2000, 11, 7))
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.orderUpdatedCalls, 4)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 27.37 - 30.69, 2))
        self.assertTrue(round(strat.getResult(), 3) == -0.108)
        self.assertTrue(round(strat.getNetProfit(), 2) == round(27.37 - 30.69, 2))
        self.assertEqual(strat.positions[0].getAge().days, 2)

    def testLongPositionAdjClose(self):
        strat = self.createStrategy()
        strat.setUseAdjustedValues(True)

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-10-13,31.00,35.75,31.00,35.63,38516200,34.84
        # 2000-10-12,63.81,64.87,61.75,63.00,50892400,30.80
        # 2000-01-19,56.13,58.25,54.00,57.13,49208800,27.93
        # 2000-01-18,107.87,114.50,105.62,111.25,66791200,27.19

        strat.addPosEntry(datetime.datetime(2000, 1, 18), strat.enterLong, BaseTestCase.TestInstrument, 1, False)
        strat.addPosExitMarket(datetime.datetime(2000, 10, 12))
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 30.31 - 27.44, 2))
        self.assertTrue(round(strat.getResult(), 3) == 0.105)
        self.assertTrue(round(strat.getNetProfit(), 2) == round(30.31 - 27.44, 2))
        self.assertEqual(strat.positions[0].getAge().days, 268)

    def testLongPositionGTC(self):
        strat = self.createStrategy()
        strat.getBroker().setCash(48)

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-02-07,59.31,60.00,58.42,59.94,44697200,29.30
        # 2000-02-04,57.63,58.25,56.81,57.81,40925000,28.26 - sell succeeds
        # 2000-02-03,55.38,57.00,54.25,56.69,55540600,27.71 - exit
        # 2000-02-02,54.94,56.00,54.00,54.31,63940400,26.55
        # 2000-02-01,51.25,54.31,50.00,54.00,57108800,26.40
        # 2000-01-31,47.94,50.13,47.06,49.95,68152400,24.42 - buy succeeds
        # 2000-01-28,51.50,51.94,46.63,47.38,86400600,23.16 - buy fails
        # 2000-01-27,55.81,56.69,50.00,51.81,61061800,25.33 - enterLong

        strat.addPosEntry(datetime.datetime(2000, 1, 27), strat.enterLong, BaseTestCase.TestInstrument, 1, True)
        strat.addPosExitMarket(datetime.datetime(2000, 2, 3))
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(48 + 57.63 - 47.94, 2))
        self.assertTrue(round(strat.getNetProfit(), 2) == round(57.63 - 47.94, 2))
        self.assertEqual(strat.positions[0].getAge().days, 4)

    def testEntryCanceled(self):
        strat = self.createStrategy()
        strat.getBroker().setCash(10)

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-01-28,51.50,51.94,46.63,47.38,86400600,23.16 - buy fails
        # 2000-01-27,55.81,56.69,50.00,51.81,61061800,25.33 - enterLong

        strat.addPosEntry(datetime.datetime(2000, 1, 27), strat.enterLong, BaseTestCase.TestInstrument, 1, False)
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.enterOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(strat.getBroker().getCash() == 10)
        self.assertTrue(strat.getNetProfit() == 0)

    def testUnrealized1(self):
        strat = self.createStrategy(True)

        # 3/Jan/2011 205300 - Enter long
        # 3/Jan/2011 205400 - entry gets filled at 127.21
        # 3/Jan/2011 210000 - last bar

        strat.addPosEntry(dt.localize(datetime.datetime(2011, 1, 3, 20, 53), pytz.utc), strat.enterLong, BaseTestCase.TestInstrument, 1, True)
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), True)
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 0)

        entryPrice = 127.21
        lastPrice = strat.getFeed().getCurrentBars()[BaseTestCase.TestInstrument].getClose()

        self.assertEqual(strat.getActivePosition().getReturn(), (lastPrice - entryPrice) / entryPrice)
        self.assertEqual(strat.getActivePosition().getPnL(), lastPrice - entryPrice)

    def testUnrealized2(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = TestStrategy(barFeed, instrument, 1000)
        strat.addPosEntry(datetime.date(2000, 12, 13), strat.enterLong, instrument, 1, False)  # Filled on 2000-12-14 at 29.25.
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), True)
        self.assertEqual(strat.getActivePosition().getPnL(), 29.06 - 29.25)
        self.assertEqual(strat.getActivePosition().getReturn(), (29.06 - 29.25) / 29.25)

    def testUnrealizedAdjusted(self):
        instrument = "orcl"
        barFeed = load_daily_barfeed(instrument)
        strat = TestStrategy(barFeed, instrument, 1000)
        strat.setUseAdjustedValues(True)
        strat.addPosEntry(datetime.date(2000, 12, 13), strat.enterLong, instrument, 1, False)  # Filled on 2000-12-14 at 28.60
        strat.run()

        self.assertEqual(strat.positions[0].isOpen(), True)
        self.assertEqual(round(strat.getActivePosition().getPnL(), 2), round(28.41 - 28.60, 2))
        self.assertEqual(round(strat.getActivePosition().getReturn(), 2), round((28.41 - 28.60) / 28.60, 2))

    def testActiveOrdersAndSharesLong(self):
        instrument = "orcl"
        testCase = self

        class Strategy(strategy.BacktestingStrategy):
            def __init__(self, barFeed, cash):
                strategy.BacktestingStrategy.__init__(self, barFeed, cash)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterLong(instrument, 1, True)
                    # The entry order should be active.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 0)
                elif self.pos.isOpen():
                    # At this point the entry order should have been filled.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 1)
                    self.pos.exitMarket()
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 1)
                else:
                    # The position was closed.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 0)

        barFeed = load_daily_barfeed(instrument)
        strat = Strategy(barFeed, 1000)
        strat.run()

        self.assertNotEqual(strat.pos, None)
        self.assertEqual(strat.pos.isOpen(), False)
        # Entered on 2000-01-04 at 115.50
        # Exit on 2000-01-05 at 101.62
        self.assertEqual(strat.pos.getPnL(),  101.62 - 115.50)

    def testIsOpen_NotClosed(self):
        strat = self.createStrategy()
        strat.addPosEntry(datetime.datetime(2000, 11, 3), strat.enterLong, BaseTestCase.TestInstrument, 1, False)
        strat.run()
        self.assertTrue(strat.getActivePosition().isOpen())

    def testPartialFillGTC1(self):
        # Open and close after entry has been fully filled.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLong, instrument, 4, True)
        strat.addPosExitMarket(datetime.datetime(2000, 1, 3))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 11)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 2))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 14)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 5))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC2(self):
        # Open and close after entry has been partially filled.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLong, instrument, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 2))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 11)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 2))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 12)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 3))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isCanceled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 2)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC3(self):
        class SkipCancelBroker(object):
            def __init__(self, decorated):
                self.__decorated = decorated

            def __getattr__(self, name):
                return getattr(self.__decorated, name)

            def cancelOrder(self, order):
                return

        # Open and close after entry has been partially filled.
        # Cancelations get skipped and the position is left open.
        # The idea is to simulate a real scenario where cancelation gets submited but the order gets
        # filled before the cancelation gets processed.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat._setBroker(SkipCancelBroker(strat.getBroker()))
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLong, instrument, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 2))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 11)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 2))

        self.assertEqual(strat.positions[0].isOpen(), True)
        self.assertEqual(strat.positions[0].getShares(), 2)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC4(self):
        class SkipFirstCancelBroker(object):
            def __init__(self, decorated):
                self.__decorated = decorated
                self.__cancelSkipped = False

            def __getattr__(self, name):
                return getattr(self.__decorated, name)

            def cancelOrder(self, order):
                if not self.__cancelSkipped:
                    self.__cancelSkipped = True
                    return
                self.__decorated.cancelOrder(order)

        # Open and close after entry has been partially filled.
        # The first cancelation get skipped and a second exit has to be requested to close the position.
        # The idea is to simulate a real scenario where cancelation gets submited but the order gets
        # filled before the cancelation gets processed.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat._setBroker(SkipFirstCancelBroker(strat.getBroker()))
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLong, instrument, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 2))
        # Retry exit.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 4))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 11)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 2))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 14)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 5))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)


class ShortPosTestCase(BaseTestCase):
    def testActiveOrdersAndSharesShort(self):
        instrument = "orcl"
        testCase = self

        class Strategy(strategy.BacktestingStrategy):
            def __init__(self, barFeed, cash):
                strategy.BacktestingStrategy.__init__(self, barFeed, cash)
                self.pos = None

            def onBars(self, bars):
                if self.pos is None:
                    self.pos = self.enterShort(instrument, 1, True)
                    # The entry order should be active.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), 0)
                elif self.pos.isOpen():
                    # At this point the entry order should have been filled.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), -1)
                    self.pos.exitMarket()
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 1)
                    testCase.assertEqual(self.pos.getShares(), -1)
                else:
                    # The position was closed.
                    testCase.assertEqual(len(self.pos.getActiveOrders()), 0)
                    testCase.assertEqual(self.pos.getShares(), 0)

        barFeed = load_daily_barfeed(instrument)
        strat = Strategy(barFeed, 1000)
        strat.run()

        self.assertNotEqual(strat.pos, None)
        self.assertEqual(strat.pos.isOpen(), False)
        # Entered on 2000-01-04 at 115.50
        # Exit on 2000-01-05 at 101.62
        self.assertEqual(strat.pos.getPnL(),  115.50 - 101.62)

    def testShortPosition(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-08,27.37,27.50,24.50,24.81,63040000,24.26
        # 2000-11-07,28.37,28.44,26.50,26.56,58950800,25.97
        # 2000-11-06,30.69,30.69,27.50,27.94,75552300,27.32
        # 2000-11-03,31.50,31.75,29.50,30.31,65020900,29.64

        strat.addPosEntry(datetime.datetime(2000, 11, 3), strat.enterShort, BaseTestCase.TestInstrument, 1, False)
        strat.addPosExitMarket(datetime.datetime(2000, 11, 7))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 30.69 - 27.37, 2))
        self.assertTrue(round(strat.getResult(), 3) == round(0.10817856, 3))
        self.assertTrue(round(strat.getNetProfit(), 2) == round(30.69 - 27.37, 2))

    def testShortPositionAdjClose(self):
        strat = self.createStrategy()
        strat.setUseAdjustedValues(True)

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-10-13,31.00,35.75,31.00,35.63,38516200,34.84
        # 2000-10-12,63.81,64.87,61.75,63.00,50892400,30.80
        # 2000-01-19,56.13,58.25,54.00,57.13,49208800,27.93
        # 2000-01-18,107.87,114.50,105.62,111.25,66791200,27.19

        strat.addPosEntry(datetime.datetime(2000, 1, 18), strat.enterShort, BaseTestCase.TestInstrument, 1, False)
        strat.addPosExitMarket(datetime.datetime(2000, 10, 12))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + 27.44 - 30.31, 2))
        self.assertTrue(round(strat.getResult(), 3) == round(-0.104591837, 3))
        self.assertTrue(round(strat.getNetProfit(), 2) == round(27.44 - 30.31, 2))

    def testShortPositionExitCanceled(self):
        strat = self.createStrategy()
        strat.getBroker().setCash(0)

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-12-08,30.06,30.62,29.25,30.06,40054100,29.39
        # 2000-12-07,29.62,29.94,28.12,28.31,41093000,27.68
        # .
        # 2000-11-29,23.19,23.62,21.81,22.87,75408100,22.36
        # 2000-11-28,23.50,23.81,22.25,22.66,43078300,22.16

        strat.addPosEntry(datetime.datetime(2000, 11, 28), strat.enterShort, BaseTestCase.TestInstrument, 1, False)
        strat.addPosExitMarket(datetime.datetime(2000, 12, 7))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == 23.19)
        self.assertTrue(strat.getNetProfit() == 0)

    def testShortPositionExitCanceledAndReSubmitted(self):
        strat = self.createStrategy()
        strat.getBroker().setCash(0)

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

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterShort, BaseTestCase.TestInstrument, 1)
        strat.addPosExitMarket(datetime.datetime(2000, 11, 14))
        strat.addPosExitMarket(datetime.datetime(2000, 11, 22))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 1)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(25.12 - 23.31, 2))

    def testUnrealized(self):
        strat = self.createStrategy(True)

        # 3/Jan/2011 205300 - Enter long
        # 3/Jan/2011 205400 - entry gets filled at 127.21
        # 3/Jan/2011 210000 - last bar

        strat.addPosEntry(dt.localize(datetime.datetime(2011, 1, 3, 20, 53), pytz.utc), strat.enterShort, BaseTestCase.TestInstrument, 1, True)
        strat.run()
        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 0)

        entryPrice = 127.21
        lastPrice = strat.getFeed().getCurrentBars()[BaseTestCase.TestInstrument].getClose()

        self.assertEqual(strat.getActivePosition().getReturn(), (entryPrice - lastPrice) / entryPrice)
        self.assertEqual(strat.getActivePosition().getPnL(), entryPrice - lastPrice)


class LimitPosTestCase(BaseTestCase):
    def testLong(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - exit filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - exitPosition
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 - entry filled
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongLimit, BaseTestCase.TestInstrument, 25, 1)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 16), 29)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == 1004)

    def testShort(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-24,23.31,24.25,23.12,24.12,22446100,23.58 - exit filled
        # 2000-11-22,23.62,24.06,22.06,22.31,53317000,21.81 - exitPosition
        # 2000-11-21,24.81,25.62,23.50,23.87,58651900,23.34
        # 2000-11-20,24.31,25.87,24.00,24.75,89783100,24.20
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - entry filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - enterShortLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 16), strat.enterShortLimit, BaseTestCase.TestInstrument, 29, 1)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 22), 24)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (29 - 23.31), 2))

    def testExitOnEntryNotFilled(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - entry canceled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - exitPosition
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongLimit, BaseTestCase.TestInstrument, 5, 1, True)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 16), 29)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000)

    def testExitTwice(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - exit filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - exitPosition using a market order (cancels the previous one).
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74 - exitPosition
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 - entry filled
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongLimit, BaseTestCase.TestInstrument, 25, 1)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 14), 100)
        strat.addPosExitMarket(datetime.datetime(2000, 11, 16))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (26.94 - 25), 2))

    def testExitCancelsEntry(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74 - exitPosition (cancels the entry).
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 -
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongLimit, BaseTestCase.TestInstrument, 5, 1, True)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 14), 100)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 0)
        self.assertEqual(strat.enterCanceledCalls, 1)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == 1000)

    def testEntryGTCExitNotGTC(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23 - GTC exitPosition (never filled)
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74 -
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 - entry filled
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongLimit, BaseTestCase.TestInstrument, 25, 1, True)
        strat.addPosExitLimit(datetime.datetime(2000, 11, 15), 100, False)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertTrue(strat.exitCanceledCalls == 1)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 - 25, 2))


class StopPosTestCase(BaseTestCase):
    def testLong(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - exit filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - exitPosition
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 - entry filled
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongStop

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongStop, BaseTestCase.TestInstrument, 25, 1)
        strat.addPosExitStop(datetime.datetime(2000, 11, 16), 26)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (26 - 25.12), 2))

    def testShort(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-24,23.31,24.25,23.12,24.12,22446100,23.58 - exit filled
        # 2000-11-22,23.62,24.06,22.06,22.31,53317000,21.81 - exitPosition
        # 2000-11-21,24.81,25.62,23.50,23.87,58651900,23.34
        # 2000-11-20,24.31,25.87,24.00,24.75,89783100,24.20
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - entry filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - enterShortStop

        strat.addPosEntry(datetime.datetime(2000, 11, 16), strat.enterShortStop, BaseTestCase.TestInstrument, 27, 1)
        strat.addPosExitStop(datetime.datetime(2000, 11, 22), 23)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (26.94 - 23.31), 2))

    def testPartialFillGTC1(self):
        # Open and close after entry has been fully filled.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 6), 15, 15, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLongStop, instrument, 12, 4, True)
        strat.addPosExitMarket(datetime.datetime(2000, 1, 4))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 12)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 3))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 15)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 6))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC2(self):
        # Open and close after entry has been partially filled.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 6), 15, 15, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLongStop, instrument, 12, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 3))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 12)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 3))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 13)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 4))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isCanceled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 2)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC3(self):
        class SkipCancelBroker(object):
            def __init__(self, decorated):
                self.__decorated = decorated

            def __getattr__(self, name):
                return getattr(self.__decorated, name)

            def cancelOrder(self, order):
                return

        # Open and close after entry has been partially filled.
        # Cancelations get skipped and the position is left open.
        # The idea is to simulate a real scenario where cancelation gets submited but the order gets
        # filled before the cancelation gets processed.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 6), 15, 15, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat._setBroker(SkipCancelBroker(strat.getBroker()))
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLongStop, instrument, 12, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 3))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 0)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 1)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 12)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 3))

        self.assertEqual(strat.positions[0].isOpen(), True)
        self.assertEqual(strat.positions[0].getShares(), 2)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)

    def testPartialFillGTC4(self):
        class SkipFirstCancelBroker(object):
            def __init__(self, decorated):
                self.__decorated = decorated
                self.__cancelSkipped = False

            def __getattr__(self, name):
                return getattr(self.__decorated, name)

            def cancelOrder(self, order):
                if not self.__cancelSkipped:
                    self.__cancelSkipped = True
                    return
                self.__decorated.cancelOrder(order)

        # Open and close after entry has been partially filled.
        # The first cancelation get skipped and a second exit has to be requested to close the position.
        # The idea is to simulate a real scenario where cancelation gets submited but the order gets
        # filled before the cancelation gets processed.
        instrument = "orcl"
        bf = TestBarFeed(bar.Frequency.DAY)
        bars = [
            bar.BasicBar(datetime.datetime(2000, 1, 1), 10, 10, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 2), 11, 11, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 3), 12, 12, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 4), 13, 13, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 5), 14, 14, 10, 10, 10, 10, bar.Frequency.DAY),
            bar.BasicBar(datetime.datetime(2000, 1, 6), 15, 15, 10, 10, 10, 10, bar.Frequency.DAY),
            ]
        bf.addBarsFromSequence(instrument, bars)
        strat = TestStrategy(bf, instrument, 1000)
        strat._setBroker(SkipFirstCancelBroker(strat.getBroker()))
        strat.addPosEntry(datetime.datetime(2000, 1, 1), strat.enterLongStop, instrument, 12, 4, True)
        # Exit the position before the entry order gets completely filled.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 3))
        # Retry exit.
        strat.addPosExitMarket(datetime.datetime(2000, 1, 5))
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertEqual(strat.exitCanceledCalls, 0)

        self.assertEqual(len(strat.posExecutionInfo), 2)
        self.assertEqual(strat.posExecutionInfo[0].getPrice(), 12)
        self.assertEqual(strat.posExecutionInfo[0].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[0].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[0].getDateTime(), datetime.datetime(2000, 1, 3))
        self.assertEqual(strat.posExecutionInfo[1].getPrice(), 15)
        self.assertEqual(strat.posExecutionInfo[1].getQuantity(), 2)
        self.assertEqual(strat.posExecutionInfo[1].getCommission(), 0)
        self.assertEqual(strat.posExecutionInfo[1].getDateTime(), datetime.datetime(2000, 1, 6))

        self.assertEqual(strat.positions[0].isOpen(), False)
        self.assertEqual(strat.positions[0].getShares(), 0)
        self.assertTrue(strat.positions[0].getEntryOrder().isFilled())
        self.assertEqual(strat.positions[0].getEntryOrder().getFilled(), 4)
        self.assertEqual(strat.positions[0].getEntryOrder().getRemaining(), 0)
        self.assertTrue(strat.positions[0].getExitOrder().isFilled())
        self.assertEqual(strat.positions[0].getExitOrder().getFilled(), 2)
        self.assertEqual(strat.positions[0].getExitOrder().getRemaining(), 0)


class StopLimitPosTestCase(BaseTestCase):
    def testLong(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - exit filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - exitPosition
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20 - entry filled
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87 - enterLongStopLimit

        strat.addPosEntry(datetime.datetime(2000, 11, 10), strat.enterLongStopLimit, BaseTestCase.TestInstrument, 25.5, 24, 1)
        strat.addPosExitStopLimit(datetime.datetime(2000, 11, 16), 27, 28)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (28 - 24), 2))

    def testShort(self):
        strat = self.createStrategy()

        # Date,Open,High,Low,Close,Volume,Adj Close
        # 2000-11-24,23.31,24.25,23.12,24.12,22446100,23.58 - exit filled
        # 2000-11-22,23.62,24.06,22.06,22.31,53317000,21.81 - exitPosition
        # 2000-11-21,24.81,25.62,23.50,23.87,58651900,23.34
        # 2000-11-20,24.31,25.87,24.00,24.75,89783100,24.20
        # 2000-11-17,26.94,29.25,25.25,28.81,59639400,28.17 - entry filled
        # 2000-11-16,28.75,29.81,27.25,27.37,37990000,26.76 - enterShortStopLimit
        # 2000-11-15,28.81,29.44,27.70,28.87,50655200,28.23
        # 2000-11-14,27.37,28.50,26.50,28.37,77496700,27.74
        # 2000-11-13,25.12,25.87,23.50,24.75,61651900,24.20
        # 2000-11-10,26.44,26.94,24.87,25.44,54614100,24.87

        strat.addPosEntry(datetime.datetime(2000, 11, 16), strat.enterShortStopLimit, BaseTestCase.TestInstrument, 27, 29, 1)
        strat.addPosExitStopLimit(datetime.datetime(2000, 11, 22), 24, 25)
        strat.run()

        self.assertEqual(strat.enterOkCalls, 1)
        self.assertEqual(strat.enterCanceledCalls, 0)
        self.assertEqual(strat.exitOkCalls, 1)
        self.assertTrue(strat.exitCanceledCalls == 0)
        self.assertTrue(round(strat.getBroker().getCash(), 2) == round(1000 + (29 - 24), 2))
