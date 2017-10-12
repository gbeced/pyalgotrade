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

from pyalgotrade.stratanalyzer import returns
from pyalgotrade import warninghelpers
from pyalgotrade import broker

import datetime


class PositionState(object):
    def onEnter(self, position):
        pass

    # Raise an exception if an order can't be submitted in the current state.
    def canSubmitOrder(self, position, order):
        raise NotImplementedError()

    def onOrderEvent(self, position, orderEvent):
        raise NotImplementedError()

    def isOpen(self, position):
        raise NotImplementedError()

    def exit(self, position, stopPrice=None, limitPrice=None, goodTillCanceled=None):
        raise NotImplementedError()


class WaitingEntryState(PositionState):
    def canSubmitOrder(self, position, order):
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
    def onEnter(self, position):
        entryDateTime = position.getEntryOrder().getExecutionInfo().getDateTime()
        position.setEntryDateTime(entryDateTime)

    def canSubmitOrder(self, position, order):
        # Only exit orders should be submitted in this state.
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

        position._submitExitOrder(stopPrice, limitPrice, goodTillCanceled)


class ClosedState(PositionState):
    def onEnter(self, position):
        # Set the exit datetime if the exit order was filled.
        if position.exitFilled():
            exitDateTime = position.getExitOrder().getExecutionInfo().getDateTime()
            position.setExitDateTime(exitDateTime)

        assert(position.getShares() == 0)
        position.getStrategy().unregisterPosition(position)

    def canSubmitOrder(self, position, order):
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
        self.__entryDateTime = None
        self.__exitOrder = None
        self.__exitDateTime = None
        self.__posTracker = returns.PositionTracker(entryOrder.getInstrumentTraits())
        self.__allOrNone = allOrNone

        self.switchState(WaitingEntryState())

        entryOrder.setGoodTillCanceled(goodTillCanceled)
        entryOrder.setAllOrNone(allOrNone)
        self.__submitAndRegisterOrder(entryOrder)
        self.__entryOrder = entryOrder

    def __submitAndRegisterOrder(self, order):
        assert(order.isInitial())

        # Check if an order can be submitted in the current state.
        self.__state.canSubmitOrder(self, order)

        # This may raise an exception, so we wan't to submit the order before moving forward and registering
        # the order in the strategy.
        self.getStrategy().getBroker().submitOrder(order)

        self.__activeOrders[order.getId()] = order
        self.getStrategy().registerPositionOrder(self, order)

    def setEntryDateTime(self, dateTime):
        self.__entryDateTime = dateTime

    def setExitDateTime(self, dateTime):
        self.__exitDateTime = dateTime

    def switchState(self, newState):
        self.__state = newState
        self.__state.onEnter(self)

    def getStrategy(self):
        return self.__strategy

    def getLastPrice(self):
        return self.__strategy.getLastPrice(self.getInstrument())

    def getActiveOrders(self):
        return list(self.__activeOrders.values())

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
        """
        Calculates cumulative percentage returns up to this point.
        If the position is not closed, these will be unrealized returns.
        """

        # Deprecated in v0.18.
        if includeCommissions is False:
            warninghelpers.deprecation_warning("includeCommissions will be deprecated in the next version.", stacklevel=2)

        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getReturn(price, includeCommissions)
        return ret

    def getPnL(self, includeCommissions=True):
        """
        Calculates PnL up to this point.
        If the position is not closed, these will be unrealized PnL.
        """

        # Deprecated in v0.18.
        if includeCommissions is False:
            warninghelpers.deprecation_warning("includeCommissions will be deprecated in the next version.", stacklevel=2)

        ret = 0
        price = self.getLastPrice()
        if price is not None:
            ret = self.__posTracker.getPnL(price=price, includeCommissions=includeCommissions)
        return ret

    def cancelEntry(self):
        """Cancels the entry order if its active."""
        if self.entryActive():
            self.getStrategy().getBroker().cancelOrder(self.getEntryOrder())

    def cancelExit(self):
        """Cancels the exit order if its active."""
        if self.exitActive():
            self.getStrategy().getBroker().cancelOrder(self.getExitOrder())

    def exitMarket(self, goodTillCanceled=None):
        """Submits a market order to close this position.

        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the position is closed (entry canceled or exit filled) this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If the entry order is active, cancellation will be requested.
        """

        self.__state.exit(self, None, None, goodTillCanceled)

    def exitLimit(self, limitPrice, goodTillCanceled=None):
        """Submits a limit order to close this position.

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
        """Submits a stop order to close this position.

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
        """Submits a stop limit order to close this position.

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

    def _submitExitOrder(self, stopPrice, limitPrice, goodTillCanceled):
        assert(not self.exitActive())

        exitOrder = self.buildExitOrder(stopPrice, limitPrice)

        # If goodTillCanceled was not set, match the entry order.
        if goodTillCanceled is None:
            goodTillCanceled = self.__entryOrder.getGoodTillCanceled()
        exitOrder.setGoodTillCanceled(goodTillCanceled)

        exitOrder.setAllOrNone(self.__allOrNone)

        self.__submitAndRegisterOrder(exitOrder)
        self.__exitOrder = exitOrder

    def onOrderEvent(self, orderEvent):
        self.__updatePosTracker(orderEvent)

        order = orderEvent.getOrder()
        if not order.isActive():
            del self.__activeOrders[order.getId()]

        # Update the number of shares.
        if orderEvent.getEventType() in (broker.OrderEvent.Type.PARTIALLY_FILLED, broker.OrderEvent.Type.FILLED):
            execInfo = orderEvent.getEventInfo()
            # roundQuantity is used to prevent bugs like the one triggered in testcases.bitstamp_test:TestCase.testRoundingBug
            if order.isBuy():
                self.__shares = order.getInstrumentTraits().roundQuantity(self.__shares + execInfo.getQuantity())
            else:
                self.__shares = order.getInstrumentTraits().roundQuantity(self.__shares - execInfo.getQuantity())

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

    def getAge(self):
        """Returns the duration in open state.

        :rtype: datetime.timedelta.

        .. note::
            * If the position is open, then the difference between the entry datetime and the datetime of the last bar is returned.
            * If the position is closed, then the difference between the entry datetime and the exit datetime is returned.
        """
        ret = datetime.timedelta()
        if self.__entryDateTime is not None:
            if self.__exitDateTime is not None:
                last = self.__exitDateTime
            else:
                last = self.__strategy.getCurrentDateTime()
            ret = last - self.__entryDateTime
        return ret


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

        super(LongPosition, self).__init__(strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getShares()
        assert(quantity > 0)
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

        super(ShortPosition, self).__init__(strategy, entryOrder, goodTillCanceled, allOrNone)

    def buildExitOrder(self, stopPrice, limitPrice):
        quantity = self.getShares() * -1
        assert(quantity > 0)
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
