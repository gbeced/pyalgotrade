# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import abc

import pyalgotrade.broker
from pyalgotrade.broker import backtesting
from pyalgotrade import observer
from pyalgotrade import dispatcher
import pyalgotrade.strategy.position
from pyalgotrade import warninghelpers
from pyalgotrade import logger


class BaseStrategy(object):
    """Base class for strategies.

    :param barFeed: The bar feed that will supply the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BaseBarFeed`.
    :param broker: The broker that will handle orders.
    :type broker: :class:`pyalgotrade.broker.Broker`.

    .. note::
        This is a base class and should not be used directly.
    """

    __metaclass__ = abc.ABCMeta

    LOGGER_NAME = "strategy"

    def __init__(self, barFeed, broker):
        self.__feed = barFeed
        self.__broker = broker
        self.__activePositions = set()
        self.__orderToPosition = {}
        self.__barsProcessedEvent = observer.Event()
        self.__analyzers = []
        self.__namedAnalyzers = {}
        self.__dispatcher = dispatcher.Dispatcher()
        self.__broker.getOrderUpdatedEvent().subscribe(self.__onOrderEvent)
        self.__feed.getNewBarsEvent().subscribe(self.__onBars)

        self.__dispatcher.getStartEvent().subscribe(self.onStart)
        self.__dispatcher.getIdleEvent().subscribe(self.onIdle)

        # It is important to dispatch broker events before feed events, specially if we're backtesting.
        self.__dispatcher.addSubject(self.__broker)
        self.__dispatcher.addSubject(self.__feed)

        # Initialize logging.
        self.__logger = logger.getLogger(BaseStrategy.LOGGER_NAME)

    # Only valid for testing purposes.
    def _setBroker(self, broker):
        self.__broker = broker

    def setUseEventDateTimeInLogs(self, useEventDateTime):
        if useEventDateTime:
            logger.Formatter.DATETIME_HOOK = self.getDispatcher().getCurrentDateTime
        else:
            logger.Formatter.DATETIME_HOOK = None

    def getLogger(self):
        return self.__logger

    def getActivePositions(self):
        return self.__activePositions

    def getOrderToPosition(self):
        return self.__orderToPosition

    def getDispatcher(self):
        return self.__dispatcher

    def getResult(self):
        return self.getBroker().getEquity()

    def getBarsProcessedEvent(self):
        return self.__barsProcessedEvent

    def getUseAdjustedValues(self):
        return False

    def registerPositionOrder(self, position, order):
        self.__activePositions.add(position)
        assert(order.isActive())  # Why register an inactive order ?
        self.__orderToPosition[order.getId()] = position

    def unregisterPositionOrder(self, position, order):
        del self.__orderToPosition[order.getId()]

    def unregisterPosition(self, position):
        assert(not position.isOpen())
        self.__activePositions.remove(position)

    def __notifyAnalyzers(self, lambdaExpression):
        for s in self.__analyzers:
            lambdaExpression(s)

    def attachAnalyzerEx(self, strategyAnalyzer, name=None):
        if strategyAnalyzer not in self.__analyzers:
            if name is not None:
                if name in self.__namedAnalyzers:
                    raise Exception("A different analyzer named '%s' was already attached" % name)
                self.__namedAnalyzers[name] = strategyAnalyzer

            strategyAnalyzer.beforeAttach(self)
            self.__analyzers.append(strategyAnalyzer)
            strategyAnalyzer.attached(self)

    def getLastPrice(self, instrument):
        ret = None
        bar = self.getFeed().getLastBar(instrument)
        if bar is not None:
            if self.getUseAdjustedValues():
                ret = bar.getAdjClose()
            else:
                ret = bar.getClose()
        return ret

    def getFeed(self):
        """Returns the :class:`pyalgotrade.barfeed.BaseBarFeed` that this strategy is using."""
        return self.__feed

    def getBroker(self):
        """Returns the :class:`pyalgotrade.broker.Broker` used to handle order executions."""
        return self.__broker

    def getCurrentDateTime(self):
        """Returns the :class:`datetime.datetime` for the current :class:`pyalgotrade.bar.Bars`."""
        ret = None
        bars = self.__feed.getCurrentBars()
        if bars:
            ret = bars.getDateTime()
        return ret

    def marketOrder(self, instrument, quantity, onClose=False, goodTillCanceled=False, allOrNone=False):
        """Places a market order.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: The amount of shares. Positive means buy, negative means sell.
        :type quantity: int/float.
        :param onClose: True if the order should be filled as close to the closing price as possible (Market-On-Close order). Default is False.
        :type onClose: boolean.
        :param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the order should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.broker.MarketOrder` submitted.
        """

        ret = None
        if quantity > 0:
            ret = self.getBroker().createMarketOrder(pyalgotrade.broker.Order.Action.BUY, instrument, quantity, onClose)
        elif quantity < 0:
            ret = self.getBroker().createMarketOrder(pyalgotrade.broker.Order.Action.SELL, instrument, quantity*-1, onClose)
        if ret:
            ret.setGoodTillCanceled(goodTillCanceled)
            ret.setAllOrNone(allOrNone)
            self.getBroker().placeOrder(ret)
        return ret

    def order(self, instrument, quantity, onClose=False, goodTillCanceled=False, allOrNone=False):
        # Deprecated since v0.15
        warninghelpers.deprecation_warning("The order method will be deprecated in the next version. Please use the marketOrder method instead.", stacklevel=2)
        return self.marketOrder(instrument, quantity, onClose, goodTillCanceled, allOrNone)

    def limitOrder(self, instrument, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Places a limit order.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: The amount of shares. Positive means buy, negative means sell.
        :type quantity: int/float.
        :param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the order should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.broker.LimitOrder` submitted.
        """

        ret = None
        if quantity > 0:
            ret = self.getBroker().createLimitOrder(pyalgotrade.broker.Order.Action.BUY, instrument, limitPrice, quantity)
        elif quantity < 0:
            ret = self.getBroker().createLimitOrder(pyalgotrade.broker.Order.Action.SELL, instrument, limitPrice, quantity*-1)
        if ret:
            ret.setGoodTillCanceled(goodTillCanceled)
            ret.setAllOrNone(allOrNone)
            self.getBroker().placeOrder(ret)
        return ret

    def stopOrder(self, instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Places a stop order.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param quantity: The amount of shares. Positive means buy, negative means sell.
        :type quantity: int/float.
        :param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the order should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.broker.StopOrder` submitted.
        """

        ret = None
        if quantity > 0:
            ret = self.getBroker().createStopOrder(pyalgotrade.broker.Order.Action.BUY, instrument, stopPrice, quantity)
        elif quantity < 0:
            ret = self.getBroker().createStopOrder(pyalgotrade.broker.Order.Action.SELL, instrument, stopPrice, quantity*-1)
        if ret:
            ret.setGoodTillCanceled(goodTillCanceled)
            ret.setAllOrNone(allOrNone)
            self.getBroker().placeOrder(ret)
        return ret

    def stopLimitOrder(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Places a stop limit order.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: The amount of shares. Positive means buy, negative means sell.
        :type quantity: int/float.
        :param goodTillCanceled: True if the order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the order should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.broker.StopLimitOrder` submitted.
        """

        ret = None
        if quantity > 0:
            ret = self.getBroker().createStopLimitOrder(pyalgotrade.broker.Order.Action.BUY, instrument, stopPrice, limitPrice, quantity)
        elif quantity < 0:
            ret = self.getBroker().createStopLimitOrder(pyalgotrade.broker.Order.Action.SELL, instrument, stopPrice, limitPrice, quantity*-1)
        if ret:
            ret.setGoodTillCanceled(goodTillCanceled)
            ret.setAllOrNone(allOrNone)
            self.getBroker().placeOrder(ret)
        return ret

    def enterLong(self, instrument, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.MarketOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.LongPosition(self, instrument, None, None, quantity, goodTillCanceled, allOrNone)

    def enterShort(self, instrument, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.MarketOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.ShortPosition(self, instrument, None, None, quantity, goodTillCanceled, allOrNone)

    def enterLongLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.LimitOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.LongPosition(self, instrument, None, limitPrice, quantity, goodTillCanceled, allOrNone)

    def enterShortLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.LimitOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.ShortPosition(self, instrument, None, limitPrice, quantity, goodTillCanceled, allOrNone)

    def enterLongStop(self, instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.StopOrder` to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.LongPosition(self, instrument, stopPrice, None, quantity, goodTillCanceled, allOrNone)

    def enterShortStop(self, instrument, stopPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.StopOrder` to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.ShortPosition(self, instrument, stopPrice, None, quantity, goodTillCanceled, allOrNone)

    def enterLongStopLimit(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a buy :class:`pyalgotrade.broker.StopLimitOrder` order to enter a long position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.LongPosition(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone)

    def enterShortStopLimit(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled=False, allOrNone=False):
        """Generates a sell short :class:`pyalgotrade.broker.StopLimitOrder` order to enter a short position.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param stopPrice: The Stop price.
        :type stopPrice: float.
        :param limitPrice: Limit price.
        :type limitPrice: float.
        :param quantity: Entry order quantity.
        :type quantity: int.
        :param goodTillCanceled: True if the entry order is good till canceled. If False then the order gets automatically canceled when the session closes.
        :type goodTillCanceled: boolean.
        :param allOrNone: True if the orders should be completely filled or not at all.
        :type allOrNone: boolean.
        :rtype: The :class:`pyalgotrade.strategy.position.Position` entered.
        """

        return pyalgotrade.strategy.position.ShortPosition(self, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone)

    def exitPosition(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        # Deprecated since v0.13
        warninghelpers.deprecation_warning("exitPosition will be deprecated in the next version. Please use the exit method in the position class instead.", stacklevel=2)
        position.exit(limitPrice, stopPrice, goodTillCanceled)

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

    def onIdle(self):
        """Override (optional) to get notified when there are no events.

       .. note::
            In a pure backtesting scenario this will not be called.
        """
        pass

    @abc.abstractmethod
    def onBars(self, bars):
        """Override (**mandatory**) to get notified when new bars are available. The default implementation raises an Exception.

        **This is the method to override to enter your trading logic and enter/exit positions**.

        :param bars: The current bars.
        :type bars: :class:`pyalgotrade.bar.Bars`.
        """
        raise NotImplementedError()

    def onOrderUpdated(self, order):
        """Override (optional) to get notified when an order gets updated.
        This is not called for orders placed using any of the enterLong or enterShort methods.

        :param order: The order updated.
        :type order: :class:`pyalgotrade.broker.Order`.
        """
        pass

    def __onOrderEvent(self, broker_, orderEvent):
        order = orderEvent.getOrder()
        pos = self.__orderToPosition.get(order.getId(), None)
        if pos is None:
            self.onOrderUpdated(order)
        else:
            # Unlink the order from the position if its not active anymore.
            if not order.isActive():
                self.unregisterPositionOrder(pos, order)

            pos.onOrderEvent(orderEvent)

    def __onBars(self, dateTime, bars):
        # THE ORDER HERE IS VERY IMPORTANT

        # 1: Let analyzers process bars.
        self.__notifyAnalyzers(lambda s: s.beforeOnBars(self, bars))

        # 2: Let the strategy process current bars and place orders.
        self.onBars(bars)

        # 3: Notify that the bars were processed.
        self.__barsProcessedEvent.emit(self, bars)

    def run(self):
        """Call once (**and only once**) to run the strategy."""
        self.__dispatcher.run()

        if self.__feed.getCurrentBars() is not None:
            self.onFinish(self.__feed.getCurrentBars())
        else:
            raise Exception("Feed was empty")

    def stop(self):
        """Stops a running strategy."""
        self.__dispatcher.stop()

    def attachAnalyzer(self, strategyAnalyzer):
        """Adds a :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`."""
        self.attachAnalyzerEx(strategyAnalyzer)

    def getNamedAnalyzer(self, name):
        return self.__namedAnalyzers.get(name, None)

    def debug(self, msg):
        """Logs a message with level DEBUG on the strategy logger."""
        self.getLogger().debug(msg)

    def info(self, msg):
        """Logs a message with level INFO on the strategy logger."""
        self.getLogger().info(msg)

    def error(self, msg):
        """Logs a message with level ERROR on the strategy logger."""
        self.getLogger().error(msg)

    def critical(self, msg):
        """Logs a message with level CRITICAL on the strategy logger."""
        self.getLogger().critical(msg)


class BacktestingStrategy(BaseStrategy):
    """Base class for backtesting strategies.

    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BaseBarFeed`.
    :param cash: The amount of cash available.
    :type cash: int/float.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, barFeed, cash=1000000):
        # The broker should subscribe to barFeed events before the strategy.
        # This is to avoid executing orders placed in the current tick.
        broker = backtesting.Broker(cash, barFeed)
        BaseStrategy.__init__(self, barFeed, broker)
        self.__useAdjustedValues = False
        self.setUseEventDateTimeInLogs(True)

    def getUseAdjustedValues(self):
        return self.__useAdjustedValues

    def setUseAdjustedValues(self, useAdjusted):
        if not self.getFeed().barsHaveAdjClose():
            raise Exception("The barfeed doesn't support adjusted close values")
        self.getBroker().setUseAdjustedValues(useAdjusted, True)
        self.__useAdjustedValues = useAdjusted


class Strategy(BacktestingStrategy):
    def __init__(self, *args, **kwargs):
        # Deprecated since v0.13
        warninghelpers.deprecation_warning("Strategy class will be deprecated in the next version. Please use BaseStrategy or BacktestingStrategy instead.", stacklevel=2)
        BacktestingStrategy.__init__(self, *args, **kwargs)
