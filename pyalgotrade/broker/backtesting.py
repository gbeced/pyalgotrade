# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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
import copy

import six

from pyalgotrade import broker
from pyalgotrade.broker import fillstrategy, InstrumentTraits
from pyalgotrade import logger
import pyalgotrade.bar
from pyalgotrade import barfeed
from pyalgotrade.currency import ISO_4217_CURRENCY_CODE_PRECISION
from pyalgotrade.instrument import Instrument, build_instrument, assert_valid_currency


######################################################################
# Commission models

@six.add_metaclass(abc.ABCMeta)
class Commission(object):
    """Base class for implementing different commission schemes.

    .. note::
        This is a base class and should not be used directly.
    """

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
        super(FixedPerTrade, self).__init__()
        self._amount = amount

    def calculate(self, order, price, quantity):
        ret = 0
        # Only charge the first fill.
        if order.getExecutionInfo() is None:
            ret = self._amount
        return ret


class TradePercentage(Commission):
    """A :class:`Commission` class that charges a percentage of the whole trade.

    :param percentage: The percentage to charge. 0.01 means 1%, and so on. It must be smaller than 1.
    :type percentage: float.
    """
    def __init__(self, percentage):
        super(TradePercentage, self).__init__()
        assert(percentage < 1)
        self._percentage = percentage

    def calculate(self, order, price, quantity):
        return order.getInstrumentTraits().round(
            price * quantity * self._percentage,
            order.getInstrument().priceCurrency
        )


class DefaultInstrumentTraits(InstrumentTraits):
    def __init__(self, defaultPrecision=0):
        self._defaultPrecision = defaultPrecision
        self._customPrecisions = {}

    def setPrecision(self, symbol, precision):
        self._customPrecisions[symbol] = precision

    def getPrecision(self, symbol):
        ret = self._customPrecisions.get(symbol, None)
        if ret is None:
            ret = ISO_4217_CURRENCY_CODE_PRECISION.get(symbol.upper(), self._defaultPrecision)
        return ret


######################################################################
# Orders

class BacktestingOrder(object):
    def __init__(self, *args, **kwargs):
        self._accepted = None

    def setAcceptedDateTime(self, dateTime):
        self._accepted = dateTime

    def getAcceptedDateTime(self):
        return self._accepted

    # Override to call the fill strategy using the concrete order type.
    # return FillInfo or None if the order should not be filled.
    def process(self, broker_, bar_):
        raise NotImplementedError()


class MarketOrder(broker.MarketOrder, BacktestingOrder):
    def __init__(self, action, instrument, quantity, onClose, instrumentTraits):
        super(MarketOrder, self).__init__(action, instrument, quantity, onClose, instrumentTraits)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillMarketOrder(broker_, self, bar_)


class LimitOrder(broker.LimitOrder, BacktestingOrder):
    def __init__(self, action, instrument, limitPrice, quantity, instrumentTraits):
        super(LimitOrder, self).__init__(action, instrument, limitPrice, quantity, instrumentTraits)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillLimitOrder(broker_, self, bar_)


class StopOrder(broker.StopOrder, BacktestingOrder):
    def __init__(self, action, instrument, stopPrice, quantity, instrumentTraits):
        super(StopOrder, self).__init__(action, instrument, stopPrice, quantity, instrumentTraits)
        self._stopHit = False

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopOrder(broker_, self, bar_)

    def setStopHit(self, stopHit):
        self._stopHit = stopHit

    def getStopHit(self):
        return self._stopHit


# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(broker.StopLimitOrder, BacktestingOrder):
    def __init__(self, action, instrument, stopPrice, limitPrice, quantity, instrumentTraits):
        super(StopLimitOrder, self).__init__(
            action, instrument, stopPrice, limitPrice, quantity, instrumentTraits
        )
        self._stopHit = False  # Set to true when the limit order is activated (stop price is hit)

    def setStopHit(self, stopHit):
        self._stopHit = stopHit

    def getStopHit(self):
        return self._stopHit

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopLimitOrder(broker_, self, bar_)


######################################################################
# Broker

class Broker(broker.Broker):
    """Backtesting broker.

    :param initialBalances: A dictionary that maps a currency/stock/etc to the account's starting balance.
    :type initialBalances: dict.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param commission: An object responsible for calculating order commissions.
    :type commission: :class:`Commission`
    :param instrumentTraits: Instrument traits.
    :type instrumentTraits: :class:`InstrumentTraits`
    """

    def __init__(self, initialBalances, barFeed, commission=NoCommission(), instrumentTraits=DefaultInstrumentTraits()):
        super(Broker, self).__init__()

        assert isinstance(initialBalances, dict), "initialBalances must be a dictionary"
        assert all([isinstance(symbol, six.string_types) for symbol in initialBalances.keys()]), \
            "Some keys are not strings"
        assert isinstance(barFeed, barfeed.BaseBarFeed), "barFeed is not a subclass of barfeed.BaseBarFeed"

        self._balances = copy.copy(initialBalances)
        self._barFeed = barFeed
        self._commission = commission
        self._instrumentTraits = instrumentTraits

        self._activeOrders = {}
        self._instrumentPrice = {}
        self._useAdjustedValues = False
        self._fillStrategy = fillstrategy.DefaultStrategy(self._instrumentTraits)
        self._logger = logger.getLogger(__name__)

        # It is VERY important that the broker subscribes to barfeed events before the strategy.
        barFeed.getNewValuesEvent().subscribe(self.onBars)
        self._nextOrderId = 1
        self._started = False

    def _getNextOrderId(self):
        ret = self._nextOrderId
        self._nextOrderId += 1
        return ret

    def _getBar(self, bars, instrument):
        ret = bars.getBar(instrument)
        if ret is None:
            ret = self._barFeed.getLastBar(instrument)
        return ret

    def _registerOrder(self, order):
        assert(order.getId() not in self._activeOrders)
        assert(order.getId() is not None)
        self._activeOrders[order.getId()] = order

    def _unregisterOrder(self, order):
        assert(order.getId() in self._activeOrders)
        assert(order.getId() is not None)
        del self._activeOrders[order.getId()]

    def getLogger(self):
        return self._logger

    def getBalances(self):
        return copy.copy(self._balances)

    def getCommission(self):
        """
        Returns the strategy used to calculate order commissions.

        :rtype: :class:`Commission`.
        """
        return self._commission

    def setCommission(self, commission):
        """
        Sets the strategy to use to calculate order commissions.

        :param commission: An object responsible for calculating order commissions.
        :type commission: :class:`Commission`.
        """

        self._commission = commission

    def getInstrumentTraits(self):
        return self._instrumentTraits

    def setFillStrategy(self, strategy):
        """
        Sets the :class:`pyalgotrade.broker.fillstrategy.FillStrategy` to use.
        """
        self._fillStrategy = strategy

    def getFillStrategy(self):
        """
        Returns the :class:`pyalgotrade.broker.fillstrategy.FillStrategy` currently set.
        """
        return self._fillStrategy

    def getUseAdjustedValues(self):
        return self._useAdjustedValues

    def setUseAdjustedValues(self, useAdjusted):
        # Deprecated since v0.15
        if not self._barFeed.barsHaveAdjClose():
            raise Exception("The barfeed doesn't support adjusted close values")
        self._useAdjustedValues = useAdjusted

    def getActiveOrders(self, instrument=None):
        if instrument is None:
            ret = list(self._activeOrders.values())
        else:
            instrument = build_instrument(instrument)
            ret = [order for order in self._activeOrders.values() if order.getInstrument() == instrument]
        return ret

    def _getCurrentDateTime(self):
        return self._barFeed.getCurrentDateTime()

    def _getPriceForInstrument(self, instrument):
        ret = None

        lastBar = self._barFeed.getLastBar(instrument)
        if lastBar is not None:
            ret = lastBar.getPrice()
        else:
            # Try using the instrument price set by setShares if its available.
            ret = self._instrumentPrice.get(instrument)

        return ret

    def setShares(self, instrument, quantity, price):
        """
        Set existing shares before the strategy starts executing.

        :param instrument: Instrument identifier.
        :type instrument: A :class:`pyalgotrade.instrument.Instrument` or a string formatted like
            QUOTE_SYMBOL/PRICE_CURRENCY.
        :param quantity: The number of shares for the given instrument.
        :param price: The price for each share.
        """

        assert not self._started, "Can't setShares once the strategy started executing"

        instrument = build_instrument(instrument)
        self._balances[instrument.symbol] = quantity
        self._instrumentPrice[instrument] = price

    def getEquity(self, currency):
        """
        Returns the portfolio value. Sum instrument*price.

        :param currency: The currency to use to calculate the value for each instrument.
        """

        assert_valid_currency(currency)

        ret = 0
        for symbol, shares in six.iteritems(self._balances):
            if shares == 0:
                continue
            if symbol == currency:
                price = 1
            else:
                price = self._getPriceForInstrument(Instrument(symbol, currency))
            if price is None:
                raise Exception("Price in %s for %s is missing" % (currency, symbol))
            ret += price * shares
        return self.getInstrumentTraits().round(ret, currency)

    # Tries to commit an order execution.
    def commitOrderExecution(self, order, dateTime, fillInfo):
        instrument = order.getInstrument()
        instrumentSymbol = instrument.symbol
        priceCurrency = instrument.priceCurrency

        # Calculate deltas.
        price = fillInfo.getPrice()
        quantity = fillInfo.getQuantity()
        if order.isBuy():
            cost = price * quantity * -1
            assert(cost < 0)
            baseDelta = quantity
        else:
            assert order.isSell()
            cost = price * quantity
            assert(cost > 0)
            baseDelta = quantity * -1

        # Update the cost with the commission.
        commission = self.getCommission().calculate(order, price, quantity)
        cost -= commission

        baseBalanceFinal = self.getInstrumentTraits().round(
            self.getBalance(instrumentSymbol) + baseDelta,
            instrumentSymbol
        )
        quoteBalanceFinal = self.getInstrumentTraits().round(
            self.getBalance(priceCurrency) + cost,
            priceCurrency
        )

        if quoteBalanceFinal >= 0:
            # Update the order before updating internal state since addExecutionInfo may raise.
            # addExecutionInfo should switch the order state.
            orderExecutionInfo = broker.OrderExecutionInfo(price, quantity, commission, dateTime)
            order.addExecutionInfo(orderExecutionInfo)

            # Commit the order execution.
            self._balances[priceCurrency] = quoteBalanceFinal
            self._balances[instrumentSymbol] = baseBalanceFinal

            # Let the strategy know that the order was filled.
            self._fillStrategy.onOrderFilled(self, order)

            # Notify the order update
            if order.isFilled():
                self._unregisterOrder(order)
                eventType = broker.OrderEvent.Type.FILLED
            else:
                assert order.isPartiallyFilled(), "Order was neither filled completely nor partially"
                eventType = broker.OrderEvent.Type.PARTIALLY_FILLED
            self.notifyOrderEvent(broker.OrderEvent(order, eventType, orderExecutionInfo))
        else:
            action = "buy" if order.isBuy() else "sell"
            self._logger.debug("Not enough %s to %s %s %s [order %s]" % (
                priceCurrency, action, order.getQuantity(), instrumentSymbol, order.getId()
            ))

    def submitOrder(self, order):
        if order.isInitial():
            order.setSubmitted(self._getNextOrderId(), self._getCurrentDateTime())
            self._registerOrder(order)

            # Switch from INITIAL -> SUBMITTED
            order.switchState(broker.Order.State.SUBMITTED)
            self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.SUBMITTED, None))
        else:
            raise Exception("The order was already processed")

    # Return True if further processing is needed.
    def _preProcessOrder(self, order, bar_):
        ret = True

        # For non-GTC orders we need to check if the order has expired.
        if not order.getGoodTillCanceled():
            expired = bar_.getDateTime().date() > order.getAcceptedDateTime().date()

            # Cancel the order if it is expired.
            if expired:
                ret = False
                self._unregisterOrder(order)
                order.switchState(broker.Order.State.CANCELED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "Expired"))

        return ret

    def _postProcessOrder(self, order, bar_):
        # For non-GTC orders and daily (or greater) bars we need to check if orders should expire right now
        # before waiting for the next bar.
        if not order.getGoodTillCanceled():
            expired = False
            if self._barFeed.getFrequency() >= pyalgotrade.bar.Frequency.DAY:
                expired = bar_.getDateTime().date() >= order.getAcceptedDateTime().date()

            # Cancel the order if it will expire in the next bar.
            if expired:
                self._unregisterOrder(order)
                order.switchState(broker.Order.State.CANCELED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "Expired"))

    def _processOrder(self, order, bar):
        if not self._preProcessOrder(order, bar):
            return

        # Double dispatch to the fill strategy using the concrete order type.
        fillInfo = order.process(self, bar)
        if fillInfo is not None:
            self.commitOrderExecution(order, bar.getDateTime(), fillInfo)

        if order.isActive():
            self._postProcessOrder(order, bar)

    def _onBarsImpl(self, order, bars):
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
                self._processOrder(order, bar_)
            else:
                # If an order is not active it should be because it was canceled in this same loop and it should
                # have been removed.
                assert(order.isCanceled())
                assert(order not in self._activeOrders)

    def onBars(self, dateTime, bars):
        # Let the fill strategy know that new bars are being processed.
        self._fillStrategy.onBars(self, bars)

        # This is to froze the orders that will be processed in this event, to avoid new getting orders introduced
        # and processed on this very same event.
        ordersToProcess = list(self._activeOrders.values())

        for order in ordersToProcess:
            # This may trigger orders to be added/removed from __activeOrders.
            self._onBarsImpl(order, bars)

    def start(self):
        super(Broker, self).start()
        self._started = True

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        # If there are no more events in the barfeed, then there is nothing left for us to do since all processing took
        # place while processing barfeed events.
        return self._barFeed.eof()

    def dispatch(self):
        # All events were already emitted while handling barfeed events.
        pass

    def peekDateTime(self):
        return None

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        # In order to properly support market-on-close with intraday feeds I'd need to know about different
        # exchange/market trading hours and support specifying routing an order to a specific exchange/market.
        # Even if I had all this in place it would be a problem while paper-trading with a live feed since
        # I can't tell if the next bar will be the last bar of the market session or not.
        if onClose is True and self._barFeed.isIntraday():
            raise Exception("Market-on-close not supported with intraday feeds")

        instrument = build_instrument(instrument)
        return MarketOrder(action, instrument, quantity, onClose, self.getInstrumentTraits())

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        instrument = build_instrument(instrument)
        return LimitOrder(action, instrument, limitPrice, quantity, self.getInstrumentTraits())

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        instrument = build_instrument(instrument)
        return StopOrder(action, instrument, stopPrice, quantity, self.getInstrumentTraits())

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        instrument = build_instrument(instrument)
        return StopLimitOrder(
            action, instrument, stopPrice, limitPrice, quantity, self.getInstrumentTraits()
        )

    def cancelOrder(self, order):
        activeOrder = self._activeOrders.get(order.getId())
        if activeOrder is None:
            raise Exception("The order is not active anymore")
        if activeOrder.isFilled():
            raise Exception("Can't cancel order that has already been filled")

        self._unregisterOrder(activeOrder)
        activeOrder.switchState(broker.Order.State.CANCELED)
        self.notifyOrderEvent(
            broker.OrderEvent(activeOrder, broker.OrderEvent.Type.CANCELED, "User requested cancellation")
        )
