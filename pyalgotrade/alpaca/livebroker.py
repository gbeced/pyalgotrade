# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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
.. moduleauthor:: Robert Lee
"""

from os import kill
import threading
import time
import alpaca

from six.moves import queue
from ws4py.websocket import EchoWebSocket

import zmq

from pyalgotrade import broker
from pyalgotrade.alpaca import httpclient
from pyalgotrade.alpaca import common
from alpaca.livefeed import EventQueuer

from observer import Event

class LiveBroker(broker.Broker):
    """An Alpaca live broker.

    The live broker listens to a ZMQ SUB socket for trade updates,
    and uses a rest connection to get account info and place trades.

    :param liveFeedAddress: Address to which the ZMQ SUB socket should be connected.
    :type liveFeedAddress: string.
    :param restConnection: An Alpaca rest connection from alpaca_trade_api.
    :type restConnection: string.
    """

    QUEUE_TIMEOUT = 0.01

    def __init__(self, liveFeedAddress, restConnection):
        super(LiveBroker, self).__init__()
        
        self._restConnection = restConnection
        
        self.__tradeMonitor = EventQueuer(liveFeedAddress)
        self.__stop = False
        
    def __getattr__(self, name):
        """Transfer methods of the underlying api rest connection to the live broker.
        """
        if hasattr(self._restConnection, name):
            return getattr(self._restConnection, name)
        else:
            raise AttributeError

    @property
    def account(self):
        return self._restConnection.getAccount()

    @property
    def cash(self):
        return self.account['cash']
    
    @property
    def openPositions(self):
        return self._restConnection.list_positions()
    
    @property
    def openOrders(self):
        orders = self._restConnection.list_orders(status = 'open') 
        orders = map(fromAlpacaOrder, orders)
        return {order['client_order_id']: order for order in orders}

    def _startTradeMonitor(self):
        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Initializing trade monitor.")
        self.__tradeMonitor.start()
        self.__stop = False  # No errors. Keep running.


    # BEGIN observer.Subject interface
    def start(self):
        super(LiveBroker, self).start()

    def stop(self):
        self.__stop = True
        common.logger.info("Shutting down trade monitor.")
        self.__tradeMonitor.stop()

    def join(self):
        pass

    def eof(self):
        return self.__stop

    def dispatch(self):
        try:
            update = self.__tradeMonitor.getQueue().get(
                block = True, timeout = LiveBroker.QUEUE_TIMEOUT)
            order = update['order']
            self.notifyOrderEvent(fromAlpacaOrder(order))

        except queue.Empty:
            pass

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # END observer.Subject interface

    # BEGIN broker.Broker interface

    def getCash(self, includeShort=True):
        return self.cash

    def getInstrumentTraits(self, instrument):
        return broker.IntegerTraits()

    def getShares(self, instrument):
        return [pos for pos in self.openPositions if pos['symbol'] == instrument]

    def getPositions(self):
        return self.openPositions

    def getActiveOrders(self, instrument=None):
        if instrument is not None:
            return [openOrder for openOrder in self.openOrders if openOrder.instrument == instrument]
        else:
            return self.openOrders

    def submitOrder(self, order):
        self._restConnection.submit_order(**toAlpacaOrder(order))

    def cancelOrder(self, order):
        self._restConnection.cancel_order(order.orderId)

        # Notify that the order was canceled.
        self.notifyOrderEvent(AlpacaOrder.OrderEvent(order, AlpacaOrder.OrderEvent.Type.CANCELED, "User requested cancellation"))

    # END broker.Broker interface

    def getClock(self):
        return self._restConnection.get_clock()
    
    def getCalendar(self, start = None, end = None):
        return self._restConnection.get_calendar(start = start, end = end)

    def getPortfolioHistory(self,
        dateStart = None, dateEnd = None, period = None,
        timeframe = None, extendedHours = None):
        return self._restConnection.get_portfolio_history(
            date_start = dateStart,
            date_end = dateEnd,
            period = period,
            timeframe = timeframe,
            extended_hours = extendedHours
        )

# Types of orders
class AlpacaOrder(broker.Order):
    """Base class for Alpaca orders.
        Contains a few more fields than the broker.Order class.
    """

    class State:
        # https://alpaca.markets/docs/trading-on-alpaca/orders/#order-lifecycle
        
        # Typical states
        NEW = 1
        PARTIALLY_FILLED = 2
        FILLED = 3
        DONE_FOR_DAY = 4
        CANCELED = 5
        EXPIRED = 6
        REPLACED = 7
        PENDING_CANCEL = 8
        PENDING_REPLACE = 9

        # Less common states
        ACCEPTED = 101
        PENDING_NEW = 102
        ACCEPTED_FOR_BIDDING = 103
        STOPPED = 104
        REJECTED = 105
        SUSPENDED = 106
        CALCULATED = 107

        @classmethod
        def toString(cls, state):
            if state == cls.NEW:
                return 'new'
            elif state == cls.PARTIALLY_FILLED:
                return 'partially_filled'
            elif state == cls.FILLED:
                return 'filled'
            elif state == cls.DONE_FOR_DAY:
                return 'done_for_day'
            elif state == cls.CANCELED:
                return 'canceled'
            elif state == cls.EXPIRED:
                return 'expired'
            elif state == cls.REPLACED:
                return 'replaced'
            elif state == cls.PENDING_CANCEL:
                return 'pending_cancel'
            elif state == cls.PENDING_REPLACE:
                return 'pending_replace'
            elif state == cls.ACCEPTED:
                return 'accepted'
            elif state == cls.PENDING_NEW:
                return 'pending_new'
            elif state == cls.ACCEPTED_FOR_BIDDING:
                return 'accepted_for_bidding'
            elif state == cls.STOPPED:
                return 'stopped'
            elif state == cls.REJECTED:
                return 'rejected'
            elif state == cls.SUSPENDED:
                return 'suspended'
            elif state == cls.CALCULATED:
                return 'calculated'
            else:
                raise Exception("Invalid state")
        
        @classmethod
        def fromString(cls, strState):
            if strState == 'new':
                return cls.NEW
            elif strState == 'partially_filled':
                return cls.PARTIALLY_FILLED
            elif strState == 'filled':
                return cls.FILLED
            elif strState == 'done_for_day':
                return cls.DONE_FOR_DAY
            elif strState == 'canceled':
                return cls.CANCELED
            elif strState == 'expired':
                return cls.EXPIRED
            elif strState == 'replaced':
                return cls.REPLACED
            elif strState == 'pending_cancel':
                return cls.PENDING_CANCEL
            elif strState == 'pending_replace':
                return cls.PENDING_REPLACE
            elif strState == 'accepted':
                return cls.ACCEPTED
            elif strState == 'pending_new':
                return cls.PENDING_NEW
            elif strState == 'accepted_for_bidding':
                return cls.ACCEPTED_FOR_BIDDING
            elif strState == 'stopped':
                return cls.STOPPED
            elif strState == 'rejected':
                return cls.REJECTED
            elif strState == 'suspended':
                return cls.SUSPENDED
            elif strState == 'calculated':
                return cls.CALCULATED
            else:
                raise Exception('Invalid order state')

    class Type(broker.Order.Type):
        # MARKET = 1
        # LIMIT = 2
        # STOP = 3
        # STOP_LIMIT = 4
        TRAILING_STOP = 5

        @classmethod
        def toString(cls, type_):
            if type_ == 'market':
                return cls.MARKET
            elif type_ == 'limit':
                return cls.LIMIT
            elif type_ == 'stop':
                return cls.STOP
            elif type_ == 'stop_limit':
                return cls.STOP_LIMIT
            elif type == 'trailing_stop':
                return cls.TRAILING_STOP
            else:
                raise Exception('Inavlid order type')

        @classmethod
        def fromString(cls, strType):
            if strType == cls.MARKET:
                return 'market'
            elif strType == cls.LIMIT:
                return 'limit'
            elif strType == cls.STOP:
                return 'stop'
            elif strType == cls.STOP_LIMIT:
                return 'stop_limit'
            elif strType == cls.TRAILING_STOP:
                return 'trailing_stop'
            else:
                raise Exception('Invalid order type')

    class OrderClass(object):
        SIMPLE = 1
        BRACKET = 2
        OCO = 3
        OTO = 4

        @classmethod
        def toString(cls, orderclass):
            if orderclass == cls.SIMPLE:
                return 'simple'
            elif orderclass == cls.BRACKET:
                return 'bracket'
            elif orderclass == cls.OCO:
                return 'oco'
            elif orderclass == cls.OTO:
                return 'oto'
            else:
                raise Exception('Inavlid order class')
        
        @classmethod
        def fromString(cls, strOrderClass):
            if strOrderClass == 'simple':
                return cls.SIMPLE
            elif strOrderClass == 'bracket':
                return cls.BRACKET
            elif strOrderClass == 'oco':
                return cls.OCO
            elif strOrderClass == 'oto':
                return cls.OTO
            else:
                raise Exception('Inavlid order class')

    class Action(broker.Order.Action):

        @classmethod
        def toString(cls, action):
            if action == 'buy':
                return cls.BUY
            elif action == 'sell':
                return cls.SELL
            else:
                raise Exception('Inavlid order action')
        
        @classmethod
        def fromString(cls, strAction):
            if strAction == cls.BUY:
                return 'buy'
            elif strAction == cls.BUY_TO_COVER:
                return 'buy'
            elif strAction == cls.SELL:
                return 'sell'
            elif strAction == cls.SELL_SHORT:
                return 'sell'
            else:
                raise Exception('Inavlid order action')

    class TimeInForce(object):
        # https://alpaca.markets/docs/trading-on-alpaca/orders/#time-in-force

        DAY = 1 # good for day
        GTC = 2 # good till canceled
        OPG = 3 # market on open / limit on open
        CLS = 4 # market on close / limt on close
        IOC = 5 # immediate or cancel
        FOK = 6 # fill or kill

        @classmethod
        def toString(cls, timeInForce):
            if timeInForce == cls.DAY:
                return 'day'
            elif timeInForce == cls.GTC:
                return 'gtc'
            elif timeInForce == cls.OPG:
                return 'opg'
            elif timeInForce == cls.CLS:
                return 'cls'
            elif timeInForce == cls.IOC:
                return 'ioc'
            elif timeInForce == cls.FOK:
                return 'fok'
            else:
                raise Exception('Inavlid order time in force')
        
        @classmethod
        def fromString(cls, strTimeInForce):
            if strTimeInForce == 'day':
                return cls.DAY
            elif strTimeInForce == 'gtc':
                return cls.GTC
            elif strTimeInForce == 'opg':
                return cls.OPG
            elif strTimeInForce == 'cls':
                return cls.CLS
            elif strTimeInForce == 'ioc':
                return cls.IOC
            elif strTimeInForce == 'fok':
                return cls.fok
            else:
                raise Exception('Inavlid order time in force')


    def __init__(
        self,
        # broker.Order attributes
        type_,
        action,
        instrument,
        quantity,
        instrumentTraits = broker.InstrumentTraits(),
        # Alpaca-specific attributes
        orderId = None,
        clientOrderId = None,
        createdAt = None,
        updatedAt = None,
        submittedAt = None,
        filledAt = None,
        expiredAt = None,
        canceledAt = None,
        failedAt = None,
        replacedAt = None,
        replacedBy = None,
        replaces = None,
        assetId = None,
        assetClass = None,
        notional = None,
        filledQuantity = None,
        filledAveragePrice = None,
        orderClass = None,
        timeInForce = None,
        limiPrice = None,
        stopPrice = None,
        extendedHours = False,
        legs = None,
        trailPercent = None,
        trailPrice = None,
        hwm = None,
        # for bracket orders
        takeProfit = None,
        stopLossStop = None,
        stopLossLimit = None
    ):
        super(AlpacaOrder, self).__init__(type_, action, instrument, quantity, instrumentTraits)
        self.orderId = orderId
        self.clientOrderId = clientOrderId
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.submittedAt = submittedAt
        self.filledAt = filledAt
        self.expiredAt = expiredAt
        self.canceledAt = canceledAt
        self.failedAt = failedAt
        self.replacedAt = replacedAt
        self.replacedBy = replacedBy
        self.replaces = replaces
        self.assetId = assetId
        self.assetClass = assetClass
        self.notional = notional
        self.filledQuantity = filledQuantity
        self.filledAveragePrice = filledAveragePrice
        self.orderClass = orderClass
        self.timeInForce = timeInForce
        self.limiPrice = limiPrice
        self.stopPrice = stopPrice
        self.extendedHours = extendedHours
        self.legs = legs
        self.trailPercent = trailPercent
        self.trailPrice = trailPrice
        self.hwm = hwm
        # for bracket orders
        self.takeProfit = takeProfit
        self.stopLossStop = stopLossStop
        self.stopLossLimit = stopLossLimit

class MarketOrder(AlpacaOrder):
    """A market order is a request to buy or sell a security at the
        currently available market price.
    """    
    def __init__(self, action, instrument, quantity = None, notional = None, **kwargs):
        super(MarketOrder, self).__init__(
            type_ = AlpacaOrder.Type.MARKET,
            action = action,
            instrument = instrument,
            quantity = quantity,
            notional = notional,
            **kwargs
        )

class LimitOrder(AlpacaOrder):
    """A limit order is an order to buy or sell at a specified price or better.
    """
    def __init__(self, action, instrument, limitPrice, quantity = None, notional = None, **kwargs):
        super(LimitOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT,
            action = action,
            instrument = instrument,
            limitPrice = limitPrice,
            quantity = quantity,
            notional = notional,
            **kwargs
        )

class StopOrder(AlpacaOrder):
    """A stop (market) order is an order to buy or sell a security
        when its price moves past a particular point,
        ensuring a higher probability of achieving a predetermined
        entry or exit price.

        NOTE: Alpaca converts buy stop orders into stop limit orders
        with a limit price that is 4% higher than a stop price < $50
        (or 2.5% higher than a stop price >= $50).
    """    
    def __init__(self, action, instrument, stopPrice, quantity = None, notional = None, **kwargs):
        super(LimitOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT,
            action = action,
            instrument = instrument,
            stopPrice = stopPrice,
            quantity = quantity,
            notional = notional,
            **kwargs
        )

class StopLimitOrder(AlpacaOrder):
    """A stop-limit order is a conditional trade over a set time frame
    that combines the features of a stop order with those of a limit order
    and is used to mitigate risk.
    """
    def __init__(self, action, instrument, stopPrice, limitPrice, quantity = None, notional = None, **kwargs):
        super(LimitOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT,
            action = action,
            instrument = instrument,
            stopPrice = stopPrice,
            limitPrice = limitPrice,
            quantity = quantity,
            notional = notional,
            **kwargs
        )

class MarketOnOpenOrder(MarketOrder):
    def __init__(self, action, instrument, quantity = None, notional = None, **kwargs):
        super(MarketOrder, self).__init__(
            type_ = AlpacaOrder.Type.MARKET,
            action = action,
            instrument = instrument,
            quantity = quantity,
            notional = notional,
            timeInForce = AlpacaOrder.TimeInForce.OPG
            **kwargs
        )

class MarketOnCloseOrder(MarketOrder):
    def __init__(self, action, instrument, quantity = None, notional = None, **kwargs):
        super(MarketOrder, self).__init__(
            type_ = AlpacaOrder.Type.MARKET,
            action = action,
            instrument = instrument,
            quantity = quantity,
            notional = notional,
            timeInForce = AlpacaOrder.TimeInForce.CLS
            **kwargs
        )

class LimitOnOpenOrder(LimitOrder):
    def __init__(self, action, instrument, limitPrice, quantity = None, notional = None, **kwargs):
        super(LimitOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT,
            action = action,
            instrument = instrument,
            limitPrice = limitPrice,
            quantity = quantity,
            notional = notional,
            timeInForce = AlpacaOrder.TimeInForce.OPG
            **kwargs
        )

class LimitOnCloseOrder(LimitOrder):
    def __init__(self, action, instrument, limitPrice, quantity = None, notional = None, **kwargs):
        super(LimitOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT,
            action = action,
            instrument = instrument,
            limitPrice = limitPrice,
            quantity = quantity,
            notional = notional,
            timeInForce = AlpacaOrder.TimeInForce.CLS
            **kwargs
        )

class BracketOrder(AlpacaOrder):
    """A bracket order is a chain of three orders that can be used to
        manage your position entry and exit.

    Args:
        openingOrder (AlpacaOrder): The opening order for the bracket order.
        takeProfitLimit (numeric): The limit price for the exiting take profit limit order.
        stopLossStop (numeric): The price to trigger the exiting stop loss order.
        stopLossLimit (numeric, Optional): The limit price for the exiting stop loss order
            if the stop loss order is a limit order.

    Returns:
        AlpacaOrder: A bracket order.
    """
    
    def __new__(cls, openingOrder, takeProfitLimit, stopLossStop, stopLossLimit = None):
        
        # check exiting order conditions
        if openingOrder.action == AlpacaOrder.Action.BUY:
            assert takeProfitLimit > stopLossStop, \
                'Take profit price must be greater than stop price for buy orders.'
        elif openingOrder.action == AlpacaOrder.Action.SELL:
            assert takeProfitLimit < stopLossStop, \
                'take profit price must be less than stop price for sell orders.'
        else:
            raise Exception('Invalid order action: {openingOrder.action}')
        
        if openingOrder.extendedHours:
            raise Exception(
                'Extended hours are not supported for bracket orders, ' + \
                'converting to regular hours order.'
            )
        
        if openingOrder.TimeInForce not in [AlpacaOrder.TimeInForce.DAY, AlpacaOrder.TimeInForce.GTC]:
            raise Exception(
                'Time in force must be "day" or "gtc".'
            )
        
        order = openingOrder
        order.takeProfitLimit = takeProfitLimit
        order.stopLossStop = stopLossStop
        order.stopLossLimit = stopLossLimit
        order.orderClass = AlpacaOrder.OrderClass.BRACKET
        
        return order

class OneCancelsOtherOrder(AlpacaOrder):
    """This is a set of two orders with the same side (buy/buy or sell/sell) and
        currently only exit order is supported.
    """
    def __init__(self, action, instrument, takeProfitLimit, stopLossStop, stopLossLimit = None):
        super(OneCancelsOtherOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT, # OCO orders must be placed as limit orders
            action = action,
            instrument = instrument,
            takeProfitLimit = takeProfitLimit,
            stopLossStop = stopLossStop,
            stopLossLimit = stopLossLimit
        )

class OneTriggersOther(AlpacaOrder):
    """OTO (One-Triggers-Other) is a variant of bracket order.
        It takes one of the take-profit or stop-loss order in addition to the entry order.
    """
    def __init__(self, action, instrument, takeProfitLimit, stopLossStop, stopLossLimit = None):
        super(OneCancelsOtherOrder, self).__init__(
            type_ = AlpacaOrder.Type.LIMIT, # OCO orders must be placed as limit orders
            action = action,
            instrument = instrument,
            takeProfitLimit = takeProfitLimit,
            stopLossStop = stopLossStop,
            stopLossLimit = stopLossLimit
        )


class OneTriggersOther(AlpacaOrder):
    """OTO (One-Triggers-Other) is a variant of bracket order.
        It takes one of the take-profit or stop-loss order in addition to the entry order.

    Args:
        openingOrder (AlpacaOrder): The opening order for the bracket order.
        takeProfitLimit (numeric, Optional): The limit price for the exiting take profit limit order.
        stopLossStop (numeric, Optional): The price to trigger the exiting stop loss order.
        stopLossLimit (numeric, Optional): The limit price for the exiting stop loss order
            if the stop loss order is a limit order.

    Returns:
        AlpacaOrder: An OTO order.
    """
    
    def __new__(cls, openingOrder, takeProfitLimit = None, stopLossStop = None, stopLossLimit = None):
        
        # check exiting order conditions        
        if openingOrder.extendedHours:
            raise Exception(
                'Extended hours are not supported for bracket orders, ' + \
                'converting to regular hours order.'
            )
        
        if openingOrder.TimeInForce not in [AlpacaOrder.TimeInForce.DAY, AlpacaOrder.TimeInForce.GTC]:
            raise Exception(
                'Time in force must be "day" or "gtc".'
            )
        
        assert (takeProfitLimit or stopLossStop) is not None, \
            'One of takeProfitLimit or stopLossStop must be present'
        
        order = openingOrder
        order.takeProfitLimit = takeProfitLimit
        order.stopLossStop = stopLossStop
        order.stopLossLimit = stopLossLimit
        order.orderClass = AlpacaOrder.OrderClass.OTO
        
        return order



# Order constructers
def fromAlpacaOrder(alpacaOrderEntity):
    # https://alpaca.markets/docs/api-documentation/api-v2/orders/#order-entity
    order = AlpacaOrder(
        type_ = AlpacaOrder.Type.fromString(alpacaOrderEntity['type']),
        action = AlpacaOrder.Action.fromString(alpacaOrderEntity['side']),
        instrument = alpacaOrderEntity['symbol'],
        quantity = alpacaOrderEntity['qty'],
        instrumentTraits = broker.IntegerTraits(),
        orderId = alpacaOrderEntity['order_id'],
        clientOrderId = alpacaOrderEntity['client_order_id'],
        createdAt = alpacaOrderEntity['created_at'],
        updatedAt = alpacaOrderEntity['updated_at'],
        submittedAt = alpacaOrderEntity['submitted_at'],
        filledAt = alpacaOrderEntity['filled_at'],
        expiredAt = alpacaOrderEntity['expired_at'],
        canceledAt = alpacaOrderEntity['canceled_at'],
        failedAt = alpacaOrderEntity['failed_at'],
        replacedAt = alpacaOrderEntity['replaced_at'],
        replacedBy = alpacaOrderEntity['replaced_by'],
        replaces = alpacaOrderEntity['replaces'],
        assetId = alpacaOrderEntity['asset_id'],
        assetClass = alpacaOrderEntity['asset_class'],
        filledQuantity = alpacaOrderEntity['filled_qty'],
        filledAveragePrice = alpacaOrderEntity['filled_avg_price'],
        orderClass = alpacaOrderEntity['order_class'],
        timeInForce = AlpacaOrder.TimeInForce.fromString(alpacaOrderEntity['time_in_force']),
        limitPrice = alpacaOrderEntity['limit_price'],
        stopPrice = alpacaOrderEntity['stop_price'],
        extendedHours = alpacaOrderEntity['extended_hours'],
        legs = alpacaOrderEntity['legs'],
        trailPercent = alpacaOrderEntity['trail_percent'],
        trailPrice = alpacaOrderEntity['trail_price'],
        hwm = alpacaOrderEntity['hwm'],
        takeProfit = alpacaOrderEntity['take_profit']['limit_price'],
        stopLossStop = alpacaOrderEntity['stop_loss']['stop_price'],
        stopLossLimit = alpacaOrderEntity['stop_loss']['limit_price']
    )
    return order

def toAlpacaOrder(order):
    """ order should be a AlpacaOrder object.
    
    see https://alpaca.markets/docs/api-documentation/api-v2/orders/#order-entity
    for details.
    """

    alpacaOrder = {
        'order_id': order.orderId,
        'symbol': order.instrument,
        'qty': order.quantity,
        'notional': order.notional,
        'side': AlpacaOrder.Action.toString(order.action),
        'type': AlpacaOrder.Type.toString(order.type_),
        'time_in_force': AlpacaOrder.TimeInForce.toString(order.timeInForce),
        'limit_price': order.limitPrice,
        'stop_price': order.stopPrice,
        'trail_price': order.trailPrice,
        'trail_percent': order.trailPercent,
        'extended_hours': order.extendedHours,
        'client_order_id': order.clientOrderId,
        'order_class': AlpacaOrder.OrderClass.toString(order.orderClass),
        'take_profit': {'limit_price': order.takeProfit},
        'stop_loss':{'stop_price': order.stopLossStop}
    }

    # for bracket / OTO orders
    if order.takeProfit is not None:
        alpacaOrder['take_profit'] = {'limit_price': order.takeProfit}
    if order.stopLossStop is not None:
        alpacaOrder['stop_loss'] = {'stop_price': order.stopLossStop}
        if order.stopLossLimit is not None:
            alpacaOrder['stop_loss']['limit_price'] = order.stopLossLimit
    
    # omit items that are None
    alpacaOrder = {k: v for k, v in alpacaOrder.items() if v is not None}

    return alpacaOrder


class AlpacaOrderEvent(broker.OrderEvent):
    """Adds Alpaca specific order states to broker.OrderEvent.
    """
    class Type(AlpacaOrder.State):
        # use order states
        pass