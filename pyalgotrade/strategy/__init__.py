# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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
from pyalgotrade.broker import backtesting
from pyalgotrade import observer
import pyalgotrade.strategy.position
from pyalgotrade import warninghelpers


class BaseStrategy(object):
    """Base class for strategies.

    :param barFeed: The bar feed that will supply the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param broker: The broker that will handle orders.
    :type broker: :class:`pyalgotrade.broker.Broker`.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, barFeed, broker):
        self.__feed = barFeed
        self.__broker = broker
        self.__activePositions = set()
        self.__orderToPosition = {}
        self.__barsProcessedEvent = observer.Event()
        self.__analyzers = []
        self.__namedAnalyzers = {}
        self.__dispatcher = observer.Dispatcher()
        self.__broker.getOrderUpdatedEvent().subscribe(self.__onOrderEvent)
        self.__feed.getNewBarsEvent().subscribe(self.__onBars)

        self.__dispatcher.getStartEvent().subscribe(self.onStart)
        self.__dispatcher.getIdleEvent().subscribe(self.onIdle)

        # It is important to dispatch broker events before feed events, specially if we're backtesting.
        self.__dispatcher.addSubject(self.__broker)
        self.__dispatcher.addSubject(self.__feed)

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
        assert(position.isOpen())  # Why register an order for a closed position ?
        self.__activePositions.add(position)
        assert(order.isActive())  # Why register an inactive order ?
        self.__orderToPosition[order.getId()] = position

    def unregisterPositionOrder(self, position, order):
        del self.__orderToPosition[order.getId()]
        if not position.isOpen():
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

    def order(self, instrument, quantity, onClose=False, goodTillCanceled=False):
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

    def enterLong(self, instrument, quantity, goodTillCanceled=False):
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
        return ret

    def enterShort(self, instrument, quantity, goodTillCanceled=False):
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
        return ret

    def enterLongLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False):
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
        return ret

    def enterShortLimit(self, instrument, limitPrice, quantity, goodTillCanceled=False):
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
        return ret

    def enterLongStop(self, instrument, stopPrice, quantity, goodTillCanceled=False):
        # TODO: Deprecate this since it doesn't make any sence to open a position with a StopOrder.
        ret = pyalgotrade.strategy.position.LongPosition(self, instrument, None, stopPrice, quantity, goodTillCanceled)
        return ret

    def enterShortStop(self, instrument, stopPrice, quantity, goodTillCanceled=False):
        # TODO: Deprecate this since it doesn't make any sence to open a position with a StopOrder.
        ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, None, stopPrice, quantity, goodTillCanceled)
        return ret

    def enterLongStopLimit(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False):
        # TODO: Deprecate this since it doesn't make any sence to open a position with a StopOrder.
        ret = pyalgotrade.strategy.position.LongPosition(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled)
        return ret

    def enterShortStopLimit(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled=False):
        # TODO: Deprecate this since it doesn't make any sence to open a position with a StopOrder.
        ret = pyalgotrade.strategy.position.ShortPosition(self, instrument, limitPrice, stopPrice, quantity, goodTillCanceled)
        return ret

    def exitPosition(self, position, limitPrice=None, stopPrice=None, goodTillCanceled=None):
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
            # Notify the position that an order was updated.
            pos.onOrderEvent(broker_, orderEvent)
            # Unlink the order to the position if its not active anymore.
            if not order.isActive():
                self.unregisterPositionOrder(pos, order)

            if pos.getEntryOrder().getId() == order.getId():
                if orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.FILLED:
                    self.onEnterOk(pos)
                elif orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.CANCELED:
                    self.onEnterCanceled(pos)
                else:
                    # Partial fills not yet supported for positions, so the only option left is that the order was accepted.
                    assert(orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.ACCEPTED)
            elif pos.getExitOrder().getId() == order.getId():
                if orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.FILLED:
                    self.onExitOk(pos)
                elif orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.CANCELED:
                    self.onExitCanceled(pos)
                else:
                    # Partial fills not yet supported for positions, so the only option left is that the order was accepted.
                    assert(orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.ACCEPTED)
            else:
                # The order used to belong to a position but it was ovewritten with a new one
                # and the previous order should have been canceled.
                assert(orderEvent.getEventType() == pyalgotrade.broker.OrderEvent.Type.CANCELED)

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


class BacktestingStrategy(BaseStrategy):
    """Base class for backtesting strategies.

    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
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
