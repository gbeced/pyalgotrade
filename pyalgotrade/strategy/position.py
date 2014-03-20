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

from pyalgotrade.stratanalyzer import returns
from pyalgotrade import warninghelpers
from pyalgotrade import broker


class PositionState(object):
    def onEnter(self, position):
        pass

    # Raise an exception if an order can't be placed in the current state.
    def canPlaceOrder(self, position, order):
        raise NotImplementedError()

    def onOrderEvent(self, position, orderEvent):
        raise NotImplementedError()

    def isOpen(self, position):
        raise NotImplementedError()

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        raise NotImplementedError()


class WaitingEntryState(PositionState):
    def canPlaceOrder(self, position, order):
        if position.entryActive():
            raise Exception("The entry order is still active")

    def onOrderEvent(self, position, orderEvent):
        # Only entry order events are valid in this state.
        assert(position.getEntryOrder().getId() == orderEvent.getOrder().getId())

        if orderEvent.getEventType() in (broker.OrderEvent.Type.FILLED, broker.OrderEvent.Type.PARTIALLY_FILLED):
            position.switchState(OpenState())
            position.getStrategy().onEnterOk(position)
        elif orderEvent.getEventType() == broker.OrderEvent.Type.CANCELED:
            assert(position.getEntryOrder().getFilled() == 0)
            position.switchState(ClosedState())
            position.getStrategy().onEnterCanceled(position)

    def isOpen(self, position):
        return True

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        assert(position.getShares() == 0)
        assert(position.getEntryOrder().isActive())
        position.getStrategy().getBroker().cancelOrder(position.getEntryOrder())


class OpenState(PositionState):
    def canPlaceOrder(self, position, order):
        # Only exit orders should be placed in this state.
        pass

    def onOrderEvent(self, position, orderEvent):
        if position.getExitOrder() and position.getExitOrder().getId() == orderEvent.getOrder().getId():
            if orderEvent.getEventType() == broker.OrderEvent.Type.FILLED:
                if position.getShares() == 0:
                    position.switchState(ClosedState())
                    position.getStrategy().onExitOk(position)
            elif orderEvent.getEventType() == broker.OrderEvent.Type.CANCELED:
                assert(position.getShares() != 0)
                position.getStrategy().onExitCanceled(position)
        elif position.getEntryOrder().getId() == orderEvent.getOrder().getId():
            # Nothing to do since the entry order may be completely filled or canceled after a partial fill.
            assert(position.getShares() != 0)
        else:
            raise Exception("Invalid order event '%s' in OpenState" % (orderEvent.getEventType()))

    def isOpen(self, position):
        return True

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        assert(position.getShares() != 0)

        # Fail if a previous exit order is active.
        if position.exitActive():
            raise Exception("Exit order is active and it should be canceled first")

        # If the entry order is active, request cancellation.
        if position.entryActive():
            position.getStrategy().getBroker().cancelOrder(position.getEntryOrder())

        position._placeExitOrder(stopPrice, limitPrice, goodTillCanceled)


class ClosedState(PositionState):
    def onEnter(self, position):
        assert(position.getShares() == 0)
        position.getStrategy().unregisterPosition(position)

    def canPlaceOrder(self, position, order):
        raise Exception("The position is closed")

    def onOrderEvent(self, position, orderEvent):
        raise Exception("Invalid order event '%s' in ClosedState" % (orderEvent.getEventType()))

    def isOpen(self, position):
        return False

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        pass


class Position(object):
    """Base class for positions.

    Positions are higher level abstractions for placing orders.
    They are escentially a pair of entry-exit orders and allow
    to track returns and PnL easier that placing orders manually.

    :param strategy: The strategy that this position belongs to.
    :type strategy: :class:`pyalgotrade.strategy.BaseStrategy`.
    :param entryOrder: The order used to enter the position.
    :type entryOrder: :class:`pyalgotrade.broker.Order`
    :param goodTillCanceled: True if the entry order should be set as good till canceled.
    :type goodTillCanceled: boolean.
    :param allOrNone: True if the orders should be completely filled or not at all.
    :type allOrNone: boolean.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, strategy, entryOrder, goodTillCanceled, allOrNone):
        # The order must be created but not submitted.
        assert(entryOrder.isInitial())

        self.__state = None
        self.__activeOrders = {}
        self.__shares = 0
        self.__strategy = strategy
        self.__entryOrder = None
        self.__exitOrder = None
        self.__posTracker = returns.PositionTracker()
        self.__allOrNone = allOrNone

        self.switchState(WaitingEntryState())

        entryOrder.setGoodTillCanceled(goodTillCanceled)
        entryOrder.setAllOrNone(allOrNone)
        self.__placeAndRegisterOrder(entryOrder)
        self.__entryOrder = entryOrder

    def __placeAndRegisterOrder(self, order):
        assert(order.isInitial())

        # Check if an order can be placed in the current state.
        self.__state.canPlaceOrder(self, order)

        # This may raise an exception, so we wan't to place the order before moving forward and registering the order in the strategy.
        self.getStrategy().getBroker().placeOrder(order)

        self.__activeOrders[order.getId()] = order
        self.getStrategy().registerPositionOrder(self, order)

    def switchState(self, newState):
        self.__state = newState
        self.__state.onEnter(self)

    def getStrategy(self):
        return self.__strategy

    def getLastPrice(self):
        return self.__strategy.getLastPrice(self.getInstrument())

    def getActiveOrders(self):
        return self.__activeOrders.values()

    def getShares(self):
        """Returns the number of shares.
        This will be a possitive number for a long position, and a negative number for a short position.

        .. note::
            If the entry order was not filled, or if the position is closed, then the number of shares will be 0.
        """
        return self.__shares

    def entryActive(self):
        """Returns True if the entry order is active."""
        return self.__entryOrder is not None and self.__entryOrder.isActive()

    def entryFilled(self):
        """Returns True if the entry order was filled."""
        return self.__entryOrder is not None and self.__entryOrder.isFilled()

    def exitActive(self):
        """Returns True if the exit order is active."""
        return self.__exitOrder is not None and self.__exitOrder.isActive()

    def exitFilled(self):
        """Returns True if the exit order was filled."""
        return self.__exitOrder is not None and self.__exitOrder.isFilled()

    def getEntryOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to enter the position."""
        return self.__entryOrder

    def getExitOrder(self):
        """Returns the :class:`pyalgotrade.broker.Order` used to exit the position. If this position hasn't been closed yet, None is returned."""
        return self.__exitOrder

    def getInstrument(self):
        """Returns the instrument used for this position."""
        return self.__entryOrder.getInstrument()

    def getReturn(self, includeCommissions=True):
        """Calculates cumulative percentage returns up to this point.
        If the position is not closed, these will be unrealized returns.

        :param includeCommissions: True to include commisions in the calculation.
        :type includeCommissions: boolean.
        """

        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getReturn(price, includeCommissions)
        return ret

    def getUnrealizedReturn(self, price=None):
        # Deprecated in v0.15.
        warninghelpers.deprecation_warning("getUnrealizedReturn will be deprecated in the next version. Please use getReturn instead.", stacklevel=2)
        if price is not None:
            raise Exception("Setting the price to getUnrealizedReturn is no longer supported")
        return self.getReturn(False)

    def getPnL(self, includeCommissions=True):
        """Calculates PnL up to this point.
        If the position is not closed, these will be unrealized PnL.

        :param includeCommissions: True to include commisions in the calculation.
        :type includeCommissions: boolean.
        """

        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getNetProfit(price, includeCommissions)
        return ret

    def getNetProfit(self, includeCommissions=True):
        # Deprecated in v0.15.
        warninghelpers.deprecation_warning("getNetProfit will be deprecated in the next version. Please use getPnL instead.", stacklevel=2)
        return self.getPnL(includeCommissions)

    def getUnrealizedNetProfit(self, price=None):
        # Deprecated in v0.15.
        warninghelpers.deprecation_warning("getUnrealizedNetProfit will be deprecated in the next version. Please use getPnL instead.", stacklevel=2)
        if price is not None:
            raise Exception("Setting the price to getUnrealizedNetProfit is no longer supported")
        return self.getPnL(False)

    def getQuantity(self):
        # Deprecated in v0.15.
        warninghelpers.deprecation_warning("getQuantity will be deprecated in the next version. Please use abs(self.getShares()) instead.", stacklevel=2)
        return abs(self.getShares())

    def cancelEntry(self):
        """Cancels the entry order if its active."""
        if self.entryActive():
            self.getStrategy().getBroker().cancelOrder(self.getEntryOrder())

    def cancelExit(self):
        """Cancels the exit order if its active."""
        if self.exitActive():
            self.getStrategy().getBroker().cancelOrder(self.getExitOrder())

    def exitMarket(self, goodTillCanceled=None):
        """Places a market order to close this position.

        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, None, None, goodTillCanceled)

    def exitLimit(self, limitPrice, goodTillCanceled=None):
        """Places a limit order to close this position.

        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, None, limitPrice, goodTillCanceled)

    def exitStop(self, stopPrice, goodTillCanceled=None):
        """Places a stop order to close this position.

        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, stopPrice, None, goodTillCanceled)

    def exitStopLimit(self, stopPrice, limitPrice, goodTillCanceled=None):
        """Places a stop limit order to close this position.

        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, stopPrice, limitPrice, goodTillCanceled)

    def exit(self, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        # Deprecated in v0.15.
        if stopPrice is None and limitPrice is None:
            warninghelpers.deprecation_warning("exit will be deprecated in the next version. Please use exitMarket instead.", stacklevel=2)
        elif stopPrice is None and limitPrice is not None:
            warninghelpers.deprecation_warning("exit will be deprecated in the next version. Please use exitLimit instead.", stacklevel=2)
        elif stopPrice is not None and limitPrice is None:
            warninghelpers.deprecation_warning("exit will be deprecated in the next version. Please use exitStop instead.", stacklevel=2)
        elif stopPrice is not None and limitPrice is not None:
            warninghelpers.deprecation_warning("exit will be deprecated in the next version. Please use exitStopLimit instead.", stacklevel=2)

        self.__state.exit(self, stopPrice, limitPrice, goodTillCanceled)

    def _placeExitOrder(self, stopPrice, limitPrice, goodTillCanceled):
        assert(not self.exitActive())

        exitOrder = self.buildExitOrder(stopPrice, limitPrice)

        # If goodTillCanceled was not set, match the entry order.
        if goodTillCanceled is None:
            goodTillCanceled = self.__entryOrder.getGoodTillCanceled()
        exitOrder.setGoodTillCanceled(goodTillCanceled)

        exitOrder.setAllOrNone(self.__allOrNone)

        self.__placeAndRegisterOrder(exitOrder)
        self.__exitOrder = exitOrder

    def onOrderEvent(self, orderEvent):
        self.__updatePosTracker(orderEvent)

        order = orderEvent.getOrder()
        if not order.isActive():
            del self.__activeOrders[order.getId()]

        # Update the number of shares.
        if orderEvent.getEventType() in (broker.OrderEvent.Type.PARTIALLY_FILLED, broker.OrderEvent.Type.FILLED):
            execInfo = orderEvent.getEventInfo()
            if order.isBuy():
                self.__shares += execInfo.getQuantity()
            else:
                self.__shares -= execInfo.getQuantity()

        self.__state.onOrderEvent(self, orderEvent)

    def __updatePosTracker(self, orderEvent):
        if orderEvent.getEventType() in (broker.OrderEvent.Type.PARTIALLY_FILLED, broker.OrderEvent.Type.FILLED):
            order = orderEvent.getOrder()
            execInfo = orderEvent.getEventInfo()
            if order.isBuy():
                self.__posTracker.buy(execInfo.getQuantity(), execInfo.getPrice(), execInfo.getCommission())
            else:
                self.__posTracker.sell(execInfo.getQuantity(), execInfo.getPrice(), execInfo.getCommission())

    def buildExitOrder(self, stopPrice, limitPrice):
        raise NotImplementedError()

    def isOpen(self):
        """Returns True if the position is open."""
        return self.__state.isOpen(self)


# This class is reponsible for order management in long positions.
class LongPosition(Position):
    def __init__(self, strategy, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone):
        if limitPrice is None and stopPrice is None:
            entryOrder = strategy.getBroker().createMarketOrder(broker.Order.Action.BUY, instrument, quantity, False)
        elif limitPrice is not None and stopPrice is None:
            entryOrder = strategy.getBroker().createLimitOrder(broker.Order.Action.BUY, instrument, limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            entryOrder = strategy.getBroker().createStopOrder(broker.Order.Action.BUY, instrument, stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            entryOrder = strategy.getBroker().createStopLimitOrder(broker.Order.Action.BUY, instrument, stopPrice, limitPrice, quantity)
        else:
            assert(False)

        Position.__init__(self, strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getShares()
        if limitPrice is None and stopPrice is None:
            ret = self.getStrategy().getBroker().createMarketOrder(broker.Order.Action.SELL, self.getInstrument(), quantity, False)
        elif limitPrice is not None and stopPrice is None:
            ret = self.getStrategy().getBroker().createLimitOrder(broker.Order.Action.SELL, self.getInstrument(), limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            ret = self.getStrategy().getBroker().createStopOrder(broker.Order.Action.SELL, self.getInstrument(), stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            ret = self.getStrategy().getBroker().createStopLimitOrder(broker.Order.Action.SELL, self.getInstrument(), stopPrice, limitPrice, quantity)
        else:
            assert(False)

        return ret


# This class is reponsible for order management in short positions.
class ShortPosition(Position):
    def __init__(self, strategy, instrument, stopPrice, limitPrice, quantity, goodTillCanceled, allOrNone):
        if limitPrice is None and stopPrice is None:
            entryOrder = strategy.getBroker().createMarketOrder(broker.Order.Action.SELL_SHORT, instrument, quantity, False)
        elif limitPrice is not None and stopPrice is None:
            entryOrder = strategy.getBroker().createLimitOrder(broker.Order.Action.SELL_SHORT, instrument, limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            entryOrder = strategy.getBroker().createStopOrder(broker.Order.Action.SELL_SHORT, instrument, stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            entryOrder = strategy.getBroker().createStopLimitOrder(broker.Order.Action.SELL_SHORT, instrument, stopPrice, limitPrice, quantity)
        else:
            assert(False)

        Position.__init__(self, strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getShares() * -1
        if limitPrice is None and stopPrice is None:
            ret = self.getStrategy().getBroker().createMarketOrder(broker.Order.Action.BUY_TO_COVER, self.getInstrument(), quantity, False)
        elif limitPrice is not None and stopPrice is None:
            ret = self.getStrategy().getBroker().createLimitOrder(broker.Order.Action.BUY_TO_COVER, self.getInstrument(), limitPrice, quantity)
        elif limitPrice is None and stopPrice is not None:
            ret = self.getStrategy().getBroker().createStopOrder(broker.Order.Action.BUY_TO_COVER, self.getInstrument(), stopPrice, quantity)
        elif limitPrice is not None and stopPrice is not None:
            ret = self.getStrategy().getBroker().createStopLimitOrder(broker.Order.Action.BUY_TO_COVER, self.getInstrument(), stopPrice, limitPrice, quantity)
        else:
            assert(False)

        return ret
