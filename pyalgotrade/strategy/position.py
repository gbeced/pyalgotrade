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

from pyalgotrade.stratanalyzer import returns
from pyalgotrade import warninghelpers
from pyalgotrade import broker


class PositionState(object):
    # Raise an exception if an order can't be placed in the current state.
    def canPlaceOrder(self, position, order):
        raise NotImplementedError()

    def onOrderEvent(self, position, orderEvent):
        raise NotImplementedError()


class WaitingEntryState(PositionState):
    def canPlaceOrder(self, position, order):
        if position.entryActive():
            raise Exception("The entry order is still active")

    def onOrderEvent(self, position, orderEvent):
        if orderEvent.getEventType() == broker.OrderEvent.Type.FILLED:
            position.switchState(OpenState())
            position.getStrategy().onEnterOk(position)
        elif orderEvent.getEventType() == broker.OrderEvent.Type.CANCELED:
            position.switchState(ClosedState())
            position.getStrategy().onEnterCanceled(position)
        elif orderEvent.getEventType() == broker.OrderEvent.Type.PARTIALLY_FILLED:
            raise Exception("Invalid order event '%s' for the current state" % (orderEvent.getEventType()))


class OpenState(PositionState):
    def canPlaceOrder(self, position, order):
        pass

    def onOrderEvent(self, position, orderEvent):
        raise Exception("Invalid order event '%s' for the current state" % (orderEvent.getEventType()))


class WaitingExitState(PositionState):
    def canPlaceOrder(self, position, order):
        raise Exception("The exit order is still active")

    def onOrderEvent(self, position, orderEvent):
        if orderEvent.getEventType() == broker.OrderEvent.Type.FILLED:
            position.switchState(ClosedState())
            position.getStrategy().onExitOk(position)
        elif orderEvent.getEventType() == broker.OrderEvent.Type.CANCELED:
            position.switchState(OpenState())
            position.getStrategy().onExitCanceled(position)
        elif orderEvent.getEventType() == broker.OrderEvent.Type.PARTIALLY_FILLED:
            raise Exception("Invalid order event '%s' for the current state" % (orderEvent.getEventType()))
 

class ClosedState(PositionState):
    def canPlaceOrder(self, position, order):
        raise Exception("The position is closed")

    def onOrderEvent(self, position, orderEvent):
        raise Exception("Invalid order event '%s' for the current state" % (orderEvent.getEventType()))

 
class Position(object):
    """Base class for positions.

    :param strategy: The strategy that this position belongs to.
    :type strategy: :class:`pyalgotrade.strategy.BaseStrategy`.
    :param entryOrder: The order used to enter the position.
    :type entryOrder: :class:`pyalgotrade.broker.Order`
    :param goodTillCanceled: True if the entry order should be set as good till canceled.
    :type goodTillCanceled: boolean.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, strategy, entryOrder, goodTillCanceled):
        # The order must be created but not submitted.
        assert(entryOrder.isInitial())

        if not entryOrder.getAllOrNone():
            raise Exception("Only all-or-none orders are supported with the position interface")

        self.__state = WaitingEntryState()
        self.__activeOrders = {}
        self.__shares = 0
        self.__strategy = strategy
        self.__entryOrder = None
        self.__exitOrder = None
        self.__posTracker = returns.PositionTracker()

        entryOrder.setGoodTillCanceled(goodTillCanceled)
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

    def exit(self, limitPrice=None, stopPrice=None, goodTillCanceled=None):
        """Generates the exit order for the position.

        :param limitPrice: The limit price.
        :type limitPrice: float.
        :param stopPrice: The stop price.
        :type stopPrice: float.
        :param goodTillCanceled: True if the exit order is good till canceled. If False then the order gets automatically canceled when the session closes. If None, then it will match the entry order.
        :type goodTillCanceled: boolean.

        .. note::
            * If the entry order was not filled yet, it will be canceled.
            * If the exit order for this position was filled, this won't have any effect.
            * If the exit order for this position is pending, an exception will be raised. The exit order should be canceled first.
            * If limitPrice is not set and stopPrice is not set, then a :class:`pyalgotrade.broker.MarketOrder` is used to exit the position.
            * If limitPrice is set and stopPrice is not set, then a :class:`pyalgotrade.broker.LimitOrder` is used to exit the position.
            * If limitPrice is not set and stopPrice is set, then a :class:`pyalgotrade.broker.StopOrder` is used to exit the position.
            * If limitPrice is set and stopPrice is set, then a :class:`pyalgotrade.broker.StopLimitOrder` is used to exit the position.
        """

        if self.getEntryOrder().isActive():
            assert(self.__shares == 0)
            self.getStrategy().getBroker().cancelOrder(self.getEntryOrder())
            return

        if self.exitFilled():
            assert(self.__shares == 0)
            return

        # Fail if a previous exit order is active.
        if self.exitActive():
            raise Exception("Exit order is active and it should be canceled first")

        exitOrder = self.buildExitOrder(limitPrice, stopPrice)

        if not exitOrder.getAllOrNone():
            raise Exception("Only all-or-none orders are supported with the position interface")

        # If goodTillCanceled was not set, match the entry order.
        if goodTillCanceled is None:
            goodTillCanceled = self.__entryOrder.getGoodTillCanceled()
        exitOrder.setGoodTillCanceled(goodTillCanceled)

        self.__placeAndRegisterOrder(exitOrder)
        self.switchState(WaitingExitState())
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

    def buildExitOrder(self, limitPrice, stopPrice):
        raise NotImplementedError()

    def isOpen(self):
        """Returns True if the position is open."""
        # Entry accepted    -> open
        # Entry canceled    -> closed
        # Entry filled        -> check exit
        #     No exit order    -> open
        #     Exit accepted    -> open
        #     Exit canceled    -> open
        #     Exit filled        -> closed

        ret = False
        if self.__entryOrder.isActive():
            ret = True
        elif self.__entryOrder.isFilled():
            if self.__exitOrder is None or not self.__exitOrder.isFilled():
                ret = True
        return ret


# This class is reponsible for order management in long positions.
class LongPosition(Position):
    def __init__(self, strategy, instrument, limitPrice, stopPrice, quantity, goodTillCanceled):
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

        entryOrder.setAllOrNone(True)
        Position.__init__(self, strategy, entryOrder, goodTillCanceled)

    def buildExitOrder(self, limitPrice, stopPrice):
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

        ret.setAllOrNone(True)
        return ret


# This class is reponsible for order management in short positions.
class ShortPosition(Position):
    def __init__(self, strategy, instrument, limitPrice, stopPrice, quantity, goodTillCanceled):
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

        entryOrder.setAllOrNone(True)
        Position.__init__(self, strategy, entryOrder, goodTillCanceled)

    def buildExitOrder(self, limitPrice, stopPrice):
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

        ret.setAllOrNone(True)
        return ret
