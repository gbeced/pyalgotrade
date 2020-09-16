import datetime

import pytest

from pyalgotrade import broker as basebroker
from pyalgotrade.bitstamp import broker
from pyalgotrade.utils import dt

from testcases.bitstamp.bitstamp_test import TestStrategy, INSTRUMENT, TestingLiveTradeFeed, PRICE_CURRENCY, SYMBOL


def test_buy_with_partial_fill():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if self.pos is None:
                self.pos = self.enterLongLimit(INSTRUMENT, 100, 1, True)

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 1000}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.pos.isOpen()
    assert round(strat.pos.getShares(), 3) == 0.3
    assert len(strat.posExecutionInfo) == 1
    assert strat.pos.getEntryOrder().getSubmitDateTime().date() == datetime.datetime.now().date()


def test_buy_and_sell_with_partial_fill1():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if self.pos is None:
                self.pos = self.enterLongLimit(INSTRUMENT, 100, 1, True)
            elif bars.getDateTime() == dt.as_utc(datetime.datetime(2000, 1, 3)):
                self.pos.exitLimit(101)

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
    barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
    barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 1000}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.pos.isOpen()
    assert round(strat.pos.getShares(), 3) == 0.1
    assert len(strat.posExecutionInfo) == 1
    assert strat.pos.getEntryOrder().getSubmitDateTime().date() == datetime.datetime.now().date()
    assert strat.pos.getExitOrder().getSubmitDateTime().date() == datetime.datetime.now().date()


def test_buy_and_sell_with_partial_fill_2():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if self.pos is None:
                self.pos = self.enterLongLimit(INSTRUMENT, 100, 1, True)
            elif bars.getDateTime() == dt.as_utc(datetime.datetime(2000, 1, 3)):
                self.pos.exitLimit(101)

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)
    barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 100, 0.2)
    barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 101, 0.2)
    barFeed.addTrade(datetime.datetime(2000, 1, 6), 1, 102, 5)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 1000}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert not strat.pos.isOpen()
    assert strat.pos.getShares() == 0
    assert len(strat.posExecutionInfo) == 2
    assert strat.pos.getEntryOrder().getSubmitDateTime().date() == datetime.datetime.now().date()
    assert strat.pos.getExitOrder().getSubmitDateTime().date() == datetime.datetime.now().date()


def test_rounding_bug_with_trades():
    # Unless proper rounding is in place 0.03 - 0.01441376 - 0.01445547 - 0.00113077 == 6.50521303491e-19
    # instead of 0.

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.pos = None

        def onBars(self, bars):
            if self.pos is None:
                self.pos = self.enterLongLimit(INSTRUMENT, 1000, 0.03, True)
            elif self.pos.entryFilled() and not self.pos.getExitOrder():
                self.pos.exitLimit(1000, True)

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 1000, 1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 1000, 0.03)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 1000, 0.01441376)
    barFeed.addTrade(datetime.datetime(2000, 1, 4), 1, 1000, 0.01445547)
    barFeed.addTrade(datetime.datetime(2000, 1, 5), 1, 1000, 0.00113077)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 1000}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert brk.getBalance(SYMBOL) == 0
    assert strat.pos.getEntryOrder().getAvgFillPrice() == 1000
    assert strat.pos.getExitOrder().getAvgFillPrice() == 1000
    assert strat.pos.getEntryOrder().getFilled() == 0.03
    assert strat.pos.getExitOrder().getFilled() == 0.03
    assert strat.pos.getEntryOrder().getRemaining() == 0
    assert strat.pos.getExitOrder().getRemaining() == 0
    assert strat.pos.getEntryOrder().getSubmitDateTime().date() == datetime.datetime.now().date()
    assert strat.pos.getExitOrder().getSubmitDateTime().date() == datetime.datetime.now().date()

    assert not strat.pos.isOpen()
    assert len(strat.posExecutionInfo) == 2
    assert strat.pos.getShares() == 0.0


def test_invalid_orders():
    barFeed = TestingLiveTradeFeed()
    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 1000}, barFeed)
    with pytest.raises(Exception):
        brk.createLimitOrder(basebroker.Order.Action.BUY, "none", 1, 1)
    with pytest.raises(Exception):
        brk.createLimitOrder(basebroker.Order.Action.SELL_SHORT, "none", 1, 1)
    with pytest.raises(Exception):
        brk.createMarketOrder(basebroker.Order.Action.BUY, "none", 1)
    with pytest.raises(Exception):
        brk.createStopOrder(basebroker.Order.Action.BUY, "none", 1, 1)
    with pytest.raises(Exception):
        brk.createStopLimitOrder(basebroker.Order.Action.BUY, "none", 1, 1, 1)


def test_buy_without_cash():
    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.errors = 0

        def onBars(self, bars):
            with pytest.raises(Exception, match="Not enough USD"):
                self.limitOrder(INSTRUMENT, 10, 3)
            self.errors += 1

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 0.1)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 101, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 0.2)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 0}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.errors == 4
    assert brk.getBalance(SYMBOL) == 0
    assert brk.getBalance(PRICE_CURRENCY) == 0


def test_ran_out_of_cash():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.errors = 0

        def onBars(self, bars):
            # The first order should work, the rest should fail.
            if self.getBroker().getBalance(PRICE_CURRENCY):
                self.limitOrder(INSTRUMENT, 100, 0.3)
            else:
                with pytest.raises(Exception, match="Not enough USD"):
                    self.limitOrder(INSTRUMENT, 100, 0.3)
                self.errors += 1

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 10)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 30.15}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.errors == 2
    assert brk.getBalance(SYMBOL) == 0.3
    assert brk.getBalance(PRICE_CURRENCY) == 0


def test_sell_without_btc():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.errors = 0

        def onBars(self, bars):
            with pytest.raises(Exception, match="Not enough BTC"):
                self.limitOrder(INSTRUMENT, 100, -0.5)
            self.errors += 1

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 0}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.errors == 2
    assert brk.getBalance(SYMBOL) == 0
    assert brk.getBalance(PRICE_CURRENCY) == 0


def test_ran_out_of_coins():

    class Strategy(TestStrategy):
        def __init__(self, feed, brk):
            TestStrategy.__init__(self, feed, brk)
            self.errors = 0
            self.bought = False

        def onBars(self, bars):
            if not self.bought:
                self.limitOrder(INSTRUMENT, 100, 0.5)
                self.bought = True
            elif self.getBroker().getBalance(SYMBOL) > 0:
                self.limitOrder(INSTRUMENT, 100, -self.getBroker().getBalance(SYMBOL))
            else:
                with pytest.raises(Exception, match="Not enough BTC"):
                    self.limitOrder(INSTRUMENT, 100, -1)
                self.errors += 1

    barFeed = TestingLiveTradeFeed()
    barFeed.addTrade(datetime.datetime(2000, 1, 1), 1, 100, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 2), 1, 100, 10)
    barFeed.addTrade(datetime.datetime(2000, 1, 3), 1, 100, 10)

    brk = broker.PaperTradingBroker({PRICE_CURRENCY: 50.5}, barFeed)
    strat = Strategy(barFeed, brk)
    strat.run()

    assert strat.errors == 1
    assert brk.getBalance(SYMBOL) == 0
    assert brk.getBalance(PRICE_CURRENCY) == 50
