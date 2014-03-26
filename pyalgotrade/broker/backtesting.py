# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
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

from pyalgotrade import broker
from pyalgotrade import warninghelpers
from pyalgotrade import logger
import pyalgotrade.bar


######################################################################
## Commission models

class Commission(object):
    """Base class for implementing different commission schemes.

    .. note::
        This is a base class and should not be used directly.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def calculate(self, order, price, quantity):
        """Calculates the commission for an order execution.

        :param order: The order being executed.
        :type order: :class:`pyalgotrade.broker.Order`.
        :param price: The price for each share.
        :type price: float.
        :param quantity: The order size.
        :type quantity: float.
        :rtype: float.
        """
        raise NotImplementedError()


class NoCommission(Commission):
    """A :class:`Commission` class that always returns 0."""

    def calculate(self, order, price, quantity):
        return 0


class FixedPerTrade(Commission):
    """A :class:`Commission` class that charges a fixed amount for the whole trade.

    :param amount: The commission for an order.
    :type amount: float.
    """
    def __init__(self, amount):
        self.__amount = amount

    def calculate(self, order, price, quantity):
        ret = 0
        # Only charge the first fill.
        if order.getExecutionInfo() is None:
            ret = self.__amount
        return ret


class TradePercentage(Commission):
    """A :class:`Commission` class that charges a percentage of the whole trade.

    :param percentage: The percentage to charge. 0.01 means 1%, and so on. It must be smaller than 1.
    :type percentage: float.
    """
    def __init__(self, percentage):
        assert(percentage < 1)
        self.__percentage = percentage

    def calculate(self, order, price, quantity):
        return price * quantity * self.__percentage


######################################################################
## Order filling strategies

# Returns the trigger price for a Stop or StopLimit order, or None if the stop price was not yet penetrated.
def get_stop_price_trigger(action, stopPrice, useAdjustedValues, bar):
    ret = None
    open_ = bar.getOpen(useAdjustedValues)
    high = bar.getHigh(useAdjustedValues)
    low = bar.getLow(useAdjustedValues)

    # If the bar is above the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
        if low > stopPrice:
            ret = open_
        elif stopPrice <= high:
            if open_ > stopPrice:  # The stop price was penetrated on open.
                ret = open_
            else:
                ret = stopPrice
    # If the bar is below the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
        if high < stopPrice:
            ret = open_
        elif stopPrice >= low:
            if open_ < stopPrice:  # The stop price was penetrated on open.
                ret = open_
            else:
                ret = stopPrice
    else:  # Unknown action
        assert(False)

    return ret


# Returns the trigger price for a Limit or StopLimit order, or None if the limit price was not yet penetrated.
def get_limit_price_trigger(action, limitPrice, useAdjustedValues, bar):
    ret = None
    open_ = bar.getOpen(useAdjustedValues)
    high = bar.getHigh(useAdjustedValues)
    low = bar.getLow(useAdjustedValues)

    # If the bar is below the limit price, use the open price.
    # If the bar includes the limit price, use the open price or the limit price.
    if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
        if high < limitPrice:
            ret = open_
        elif limitPrice >= low:
            if open_ < limitPrice:  # The limit price was penetrated on open.
                ret = open_
            else:
                ret = limitPrice
    # If the bar is above the limit price, use the open price.
    # If the bar includes the limit price, use the open price or the limit price.
    elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
        if low > limitPrice:
            ret = open_
        elif limitPrice <= high:
            if open_ > limitPrice:  # The limit price was penetrated on open.
                ret = open_
            else:
                ret = limitPrice
    else:  # Unknown action
        assert(False)
    return ret


class FillInfo(object):
    def __init__(self, price, quantity):
        self.__price = price
        self.__quantity = quantity

    def getPrice(self):
        return self.__price

    def getQuantity(self):
        return self.__quantity


class FillStrategy(object):
    """Base class for order filling strategies."""

    __metaclass__ = abc.ABCMeta

    def onBars(self, dateTime, bars):
        """Override (optional) to get notified when the broker is about to process new bars."""
        pass

    def onOrderFilled(self, order):
        """Override (optional) to get notified when an order was filled, or partially filled."""
        pass

    @abc.abstractmethod
    def fillMarketOrder(self, order, broker_, bar):
        """Override to return the fill price and quantity for a market order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.MarketOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillLimitOrder(self, order, broker_, bar):
        """Override to return the fill price and quantity for a limit order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.LimitOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillStopOrder(self, order, broker_, bar):
        """Override to return the fill price and quantity for a stop order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillStopLimitOrder(self, order, broker_, bar):
        """Override to return the fill price and quantity for a stop limit order or None if the order can't be filled at the given time.

        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopLimitOrder`.
        :param broker_: The broker.
        :type broker_: :class:`Broker`.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()


class DefaultStrategy(FillStrategy):
    """
    Default fill strategy.

    :param volumeLimit: The proportion of the volume that orders can take up in a bar. Must be > 0 and <= 1.
    :type volumeLimit: float.

    This strategy works as follows:

    * A :class:`pyalgotrade.broker.MarketOrder` is always filled using the open/close price.
    * A :class:`pyalgotrade.broker.LimitOrder` will be filled like this:
        * If the limit price was penetrated with the open price, then the open price is used.
        * If the bar includes the limit price, then the limit price is used.
        * Note that when buying the price is penetrated if it gets <= the limit price, and when selling the price is penetrated
          if it gets >= the limit price
    * A :class:`pyalgotrade.broker.StopOrder` will be filled like this:
        * If the stop price was penetrated with the open price, then the open price is used.
        * If the bar includes the stop price, then the stop price is used.
        * Note that when buying the price is penetrated if it gets >= the stop price, and when selling the price is penetrated
          if it gets <= the stop price
    * A :class:`pyalgotrade.broker.StopLimitOrder` will be filled like this:
        * If the stop price was penetrated with the open price, or if the bar includes the stop price, then the limit order becomes active.
        * If the limit order is active:
            * If the limit order was activated in this same bar and the limit price is penetrated as well, then the best between
              the stop price and the limit fill price (as described earlier) is used.
            * If the limit order was activated at a previous bar then the limit fill price (as described earlier) is used.

    .. note::
        * This is the default strategy used by the Broker.
        * If volumeLimit is 0.25, and a certain bar's volume is 100, then no more than 25 shares can be used by all
          orders that get processed at that bar.
        * If using trade bars, then all the volume from that bar can be used.
    """

    def __init__(self, volumeLimit=0.25):
        assert(volumeLimit > 0 and volumeLimit <= 1)
        self.__volumeLimit = volumeLimit
        self.__volumeLeft = {}

    def onBars(self, dateTime, bars):
        # Update the volume available for each instrument.
        volumeLeft = {}
        for instrument in bars.getInstruments():
            bar = bars[instrument]
            if bar.getFrequency() == pyalgotrade.bar.Frequency.TRADE:
                volumeLeft[instrument] = bar.getVolume()
            elif self.__volumeLimit is not None:
                volumeLeft[instrument] = bar.getVolume() * self.__volumeLimit
        self.__volumeLeft = volumeLeft

    def onOrderFilled(self, order):
        # Update the volume left.
        if self.__volumeLimit is not None:
            self.__volumeLeft[order.getInstrument()] -= order.getExecutionInfo().getQuantity()

    def setVolumeLimit(self, volumeLimit):
        self.__volumeLimit = volumeLimit

    def __calculateFillSize(self, order, broker_, bar):
        ret = 0

        # If self.__volumeLimit then allow all the order to get filled.
        if self.__volumeLimit is not None:
            volumeLeft = self.__volumeLeft.get(order.getInstrument(), 0)
        else:
            volumeLeft = order.getRemaining()

        if not broker_.getAllowFractions():
            volumeLeft = int(volumeLeft)

        if not order.getAllOrNone():
            ret = min(volumeLeft, order.getRemaining())
        elif order.getRemaining() <= volumeLeft:
            ret = order.getRemaining()

        return ret

    def fillMarketOrder(self, order, broker_, bar):
        fillSize = self.__calculateFillSize(order, broker_, bar)
        if fillSize == 0:
            return None

        ret = None
        if order.getFillOnClose():
            price = bar.getClose(broker_.getUseAdjustedValues())
        else:
            price = bar.getOpen(broker_.getUseAdjustedValues())
        if price is not None:
            ret = FillInfo(price, fillSize)
        return ret

    def fillLimitOrder(self, order, broker_, bar):
        fillSize = self.__calculateFillSize(order, broker_, bar)
        if fillSize == 0:
            return None

        ret = None
        price = get_limit_price_trigger(order.getAction(), order.getLimitPrice(), broker_.getUseAdjustedValues(), bar)
        if price is not None:
            ret = FillInfo(price, fillSize)
        return ret

    def fillStopOrder(self, order, broker_, bar):
        ret = None

        # First check if the stop price was hit so the market order becomes active.
        stopPriceTrigger = None
        if not order.getStopHit():
            stopPriceTrigger = get_stop_price_trigger(order.getAction(), order.getStopPrice(), broker_.getUseAdjustedValues(), bar)
            order.setStopHit(stopPriceTrigger is not None)

        # If the stop price was hit, check if we can fill the market order.
        if order.getStopHit():
            fillSize = self.__calculateFillSize(order, broker_, bar)
            if fillSize == 0:
                return None

            # If we just hit the stop price we'll use it as the fill price.
            # For the remaining bars we'll use the open price.
            if stopPriceTrigger is not None:
                price = stopPriceTrigger
            else:
                price = bar.getOpen(broker_.getUseAdjustedValues())

            ret = FillInfo(price, fillSize)
        return ret

    def fillStopLimitOrder(self, order, broker_, bar):
        ret = None

        # First check if the stop price was hit so the limit order becomes active.
        stopPriceTrigger = None
        if not order.getStopHit():
            stopPriceTrigger = get_stop_price_trigger(order.getAction(), order.getStopPrice(), broker_.getUseAdjustedValues(), bar)
            order.setStopHit(stopPriceTrigger is not None)

        # If the stop price was hit, check if we can fill the limit order.
        if order.getStopHit():
            fillSize = self.__calculateFillSize(order, broker_, bar)
            if fillSize == 0:
                return None

            price = get_limit_price_trigger(order.getAction(), order.getLimitPrice(), broker_.getUseAdjustedValues(), bar)
            if price is not None:
                # If we just hit the stop price, we need to make additional checks.
                if stopPriceTrigger is not None:
                    if order.isBuy():
                        # If the stop price triggered is lower than the limit price, then use that one. Else use the limit price.
                        price = min(stopPriceTrigger, order.getLimitPrice())
                    else:
                        # If the stop price triggered is greater than the limit price, then use that one. Else use the limit price.
                        price = max(stopPriceTrigger, order.getLimitPrice())

                ret = FillInfo(price, fillSize)

        return ret


######################################################################
## Orders

class BacktestingOrder(object):
    def __init__(self):
        self.__accepted = None

    def setAcceptedDateTime(self, dateTime):
        self.__accepted = dateTime

    def getAcceptedDateTime(self):
        return self.__accepted

    # Override to call the fill strategy using the concrete order type.
    # return FillInfo or None if the order should not be filled.
    def process(self, broker_, bar_):
        raise NotImplementedError()


class MarketOrder(broker.MarketOrder, BacktestingOrder):
    def __init__(self, orderId, action, instrument, quantity, onClose):
        broker.MarketOrder.__init__(self, orderId, action, instrument, quantity, onClose)
        BacktestingOrder.__init__(self)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillMarketOrder(self, broker_, bar_)


class LimitOrder(broker.LimitOrder, BacktestingOrder):
    def __init__(self, orderId, action, instrument, limitPrice, quantity):
        broker.LimitOrder.__init__(self, orderId, action, instrument, limitPrice, quantity)
        BacktestingOrder.__init__(self)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillLimitOrder(self, broker_, bar_)


class StopOrder(broker.StopOrder, BacktestingOrder):
    def __init__(self, orderId, action, instrument, stopPrice, quantity):
        broker.StopOrder.__init__(self, orderId, action, instrument, stopPrice, quantity)
        BacktestingOrder.__init__(self)
        self.__stopHit = False

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopOrder(self, broker_, bar_)

    def setStopHit(self, stopHit):
        self.__stopHit = stopHit

    def getStopHit(self):
        return self.__stopHit


# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(broker.StopLimitOrder, BacktestingOrder):
    def __init__(self, orderId, action, instrument, stopPrice, limitPrice, quantity):
        broker.StopLimitOrder.__init__(self, orderId, action, instrument, stopPrice, limitPrice, quantity)
        BacktestingOrder.__init__(self)
        self.__stopHit = False  # Set to true when the limit order is activated (stop price is hit)

    def setStopHit(self, stopHit):
        self.__stopHit = stopHit

    def getStopHit(self):
        return self.__stopHit

    def isLimitOrderActive(self):
        # TODO: Deprecated since v0.15. Use getStopHit instead.
        return self.__stopHit

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopLimitOrder(self, broker_, bar_)


######################################################################
## Broker

class Broker(broker.Broker):
    """Backtesting broker.

    :param cash: The initial amount of cash.
    :type cash: int/float.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param commission: An object responsible for calculating order commissions.
    :type commission: :class:`Commission`
    """

    LOGGER_NAME = "broker.backtesting"

    def __init__(self, cash, barFeed, commission=None):
        broker.Broker.__init__(self)

        assert(cash >= 0)
        self.__cash = cash
        if commission is None:
            self.__commission = NoCommission()
        else:
            self.__commission = commission
        self.__shares = {}
        self.__activeOrders = {}
        self.__useAdjustedValues = False
        self.__fillStrategy = DefaultStrategy()
        self.__allowFractions = False
        self.__logger = logger.getLogger(Broker.LOGGER_NAME)

        # It is VERY important that the broker subscribes to barfeed events before the strategy.
        barFeed.getNewBarsEvent().subscribe(self.onBars)
        self.__barFeed = barFeed
        self.__allowNegativeCash = False
        self.__nextOrderId = 1

    def __getNextOrderId(self):
        ret = self.__nextOrderId
        self.__nextOrderId += 1
        return ret

    def __getBar(self, bars, instrument):
        ret = bars.getBar(instrument)
        if ret is None:
            ret = self.__barFeed.getLastBar(instrument)
        return ret

    def getLogger(self):
        return self.__logger

    def setAllowFractions(self, allowFractions):
        self.__allowFractions = allowFractions

    def getAllowFractions(self):
        return self.__allowFractions

    def setAllowNegativeCash(self, allowNegativeCash):
        self.__allowNegativeCash = allowNegativeCash

    def getCash(self, includeShort=True):
        """
        Returns the available cash.

        :param includeShort: Include cash from short positions.
        :type includeShort: boolean.
        """
        ret = self.__cash
        if not includeShort and self.__barFeed.getCurrentBars() is not None:
            bars = self.__barFeed.getCurrentBars()
            for instrument, shares in self.__shares.iteritems():
                if shares < 0:
                    instrumentPrice = self.__getBar(bars, instrument).getClose(self.getUseAdjustedValues())
                    ret += instrumentPrice * shares
        return ret

    def setCash(self, cash):
        self.__cash = cash

    def getCommission(self):
        """Returns the strategy used to calculate order commissions.

        :rtype: :class:`Commission`.
        """
        return self.__commission

    def setCommission(self, commission):
        """Sets the strategy to use to calculate order commissions.

        :param commission: An object responsible for calculating order commissions.
        :type commission: :class:`Commission`.
        """

        self.__commission = commission

    def setFillStrategy(self, strategy):
        """Sets the :class:`FillStrategy` to use."""
        self.__fillStrategy = strategy

    def getFillStrategy(self):
        """Returns the :class:`FillStrategy` currently set."""
        return self.__fillStrategy

    def getUseAdjustedValues(self):
        return self.__useAdjustedValues

    def setUseAdjustedValues(self, useAdjusted, deprecationCheck=None):
        # Deprecated since v0.15
        if not self.__barFeed.barsHaveAdjClose():
            raise Exception("The barfeed doesn't support adjusted close values")
        if deprecationCheck is None:
            warninghelpers.deprecation_warning("setUseAdjustedValues will be deprecated in the next version. Please use setUseAdjustedValues on the strategy instead.", stacklevel=2)
        self.__useAdjustedValues = useAdjusted

    def getActiveOrders(self, instrument=None):
        if instrument is None:
            ret = self.__activeOrders.values()
        else:
            ret = [order for order in self.__activeOrders.values() if order.getInstrument() == instrument]
        return ret

    def getPendingOrders(self):
        warninghelpers.deprecation_warning("getPendingOrders will be deprecated in the next version. Please use getActiveOrders instead.", stacklevel=2)
        return self.getActiveOrders()

    def getShares(self, instrument):
        return self.__shares.get(instrument, 0)

    def getPositions(self):
        return self.__shares

    def getActiveInstruments(self):
        return [instrument for instrument, shares in self.__shares.iteritems() if shares != 0]

    def __getEquityWithBars(self, bars):
        ret = self.getCash()
        if bars is not None:
            for instrument, shares in self.__shares.iteritems():
                instrumentPrice = self.__getBar(bars, instrument).getClose(self.getUseAdjustedValues())
                ret += instrumentPrice * shares
        return ret

    def getValue(self, deprecated=None):
        if deprecated is not None:
            warninghelpers.deprecation_warning("The bars parameter is no longer used and will be removed in the next version.", stacklevel=2)

        return self.__getEquityWithBars(self.__barFeed.getCurrentBars())

    def getEquity(self):
        """Returns the portfolio value (cash + shares)."""
        return self.__getEquityWithBars(self.__barFeed.getCurrentBars())

    # Tries to commit an order execution. Returns True if the order was commited, or False is there is not enough cash.
    def commitOrderExecution(self, order, dateTime, fillInfo):
        price = fillInfo.getPrice()
        quantity = fillInfo.getQuantity()

        if order.isBuy():
            cost = price * quantity * -1
            assert(cost < 0)
            sharesDelta = quantity
        elif order.isSell():
            cost = price * quantity
            assert(cost > 0)
            sharesDelta = quantity * -1
        else:  # Unknown action
            assert(False)

        commission = self.getCommission().calculate(order, price, quantity)
        cost -= commission
        resultingCash = self.getCash() + cost

        # Check that we're ok on cash after the commission.
        if resultingCash >= 0 or self.__allowNegativeCash:

            # Update the order before updating internal state since addExecutionInfo may raise.
            # addExecutionInfo should switch the order state.
            orderExecutionInfo = broker.OrderExecutionInfo(price, quantity, commission, dateTime)
            order.addExecutionInfo(orderExecutionInfo)

            # Commit the order execution.
            self.__cash = resultingCash
            self.__shares[order.getInstrument()] = self.getShares(order.getInstrument()) + sharesDelta

            # Let the strategy know that the order was filled.
            self.__fillStrategy.onOrderFilled(order)

            # Notify the order update
            if order.isFilled():
                del self.__activeOrders[order.getId()]
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.FILLED, orderExecutionInfo))
            elif order.isPartiallyFilled():
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.PARTIALLY_FILLED, orderExecutionInfo))
            else:
                assert(False)
        else:
            self.__logger.debug("Not enough money to fill order %s" % (order))

    def placeOrder(self, order):
        if order.isInitial():
            # assert(order.getId() not in self.__activeOrders)
            self.__activeOrders[order.getId()] = order
            # Switch from INITIAL -> SUBMITTED
            # IMPORTANT: Do not emit an event for this switch because when using the position interface
            # the order is not yet mapped to the position and Position.onOrderUpdated will get called.
            order.switchState(broker.Order.State.SUBMITTED)
        else:
            raise Exception("The order was already processed")

    # Return True if further processing is needed.
    def __preProcessOrder(self, order, bar_):
        ret = True

        # For non-GTC orders we need to check if the order has expired.
        if not order.getGoodTillCanceled():
            expired = bar_.getDateTime().date() > order.getAcceptedDateTime().date()

            # Cancel the order if it is expired.
            if expired:
                ret = False
                del self.__activeOrders[order.getId()]
                order.switchState(broker.Order.State.CANCELED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "Expired"))

        return ret

    def __postProcessOrder(self, order, bar_):
        # For non-GTC orders and daily (or greater) bars we need to check if orders should expire right now
        # before waiting for the next bar.
        if not order.getGoodTillCanceled():
            expired = False
            if self.__barFeed.getFrequency() >= pyalgotrade.bar.Frequency.DAY:
                expired = bar_.getDateTime().date() >= order.getAcceptedDateTime().date()

            # Cancel the order if it will expire in the next bar.
            if expired:
                del self.__activeOrders[order.getId()]
                order.switchState(broker.Order.State.CANCELED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "Expired"))

    def __processOrder(self, order, bar_):
        if not self.__preProcessOrder(order, bar_):
            return

        # Double dispatch to the fill strategy using the concrete order type.
        fillInfo = order.process(self, bar_)
        if fillInfo is not None:
            self.commitOrderExecution(order, bar_.getDateTime(), fillInfo)

        if order.isActive():
            self.__postProcessOrder(order, bar_)

    def __onBarsImpl(self, order, bars):
        # IF WE'RE DEALING WITH MULTIPLE INSTRUMENTS WE SKIP ORDER PROCESSING IF THERE IS NO BAR FOR THE ORDER'S
        # INSTRUMENT TO GET THE SAME BEHAVIOUR AS IF WERE BE PROCESSING ONLY ONE INSTRUMENT.
        bar_ = bars.getBar(order.getInstrument())
        if bar_ is not None:
            # Switch from SUBMITTED -> ACCEPTED
            if order.isSubmitted():
                order.setAcceptedDateTime(bar_.getDateTime())
                order.switchState(broker.Order.State.ACCEPTED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.ACCEPTED, None))

            if order.isActive():
                # This may trigger orders to be added/removed from __activeOrders.
                self.__processOrder(order, bar_)
            else:
                # If an order is not active it should be because it was canceled in this same loop and it should have been removed.
                assert(order.isCanceled())
                assert(order not in self.__activeOrders)

    def onBars(self, dateTime, bars):
        # Let the strategy know that new bars are being processed.
        self.__fillStrategy.onBars(dateTime, bars)

        # This is to froze the orders that will be processed in this event, to avoid new getting orders introduced
        # and processed on this very same event.
        ordersToProcess = self.__activeOrders.values()

        for order in ordersToProcess:
            # This may trigger orders to be added/removed from __activeOrders.
            self.__onBarsImpl(order, bars)

    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        # If there are no more events in the barfeed, then there is nothing left for us to do since all processing took
        # place while processing barfeed events.
        return self.__barFeed.eof()

    def dispatch(self):
        # All events were already emitted while handling barfeed events.
        pass

    def peekDateTime(self):
        return None

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        return MarketOrder(self.__getNextOrderId(), action, instrument, quantity, onClose)

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        return LimitOrder(self.__getNextOrderId(), action, instrument, limitPrice, quantity)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        return StopOrder(self.__getNextOrderId(), action, instrument, stopPrice, quantity)

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        return StopLimitOrder(self.__getNextOrderId(), action, instrument, stopPrice, limitPrice, quantity)

    def cancelOrder(self, order):
        activeOrder = self.__activeOrders.get(order.getId())
        if activeOrder is None:
            raise Exception("The order is not active anymore")
        if activeOrder.isFilled():
            raise Exception("Can't cancel order that has already been filled")

        del self.__activeOrders[activeOrder.getId()]
        activeOrder.switchState(broker.Order.State.CANCELED)
        self.notifyOrderEvent(broker.OrderEvent(activeOrder, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))
