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
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import threading
import time
import copy

from six.moves import queue

from pyalgotrade import broker
from pyalgotrade.bitstamp import httpclient
from pyalgotrade.bitstamp import common


def build_order_from_open_order(openOrder, instrumentTraits):
    if openOrder.isBuy():
        action = broker.Order.Action.BUY
    elif openOrder.isSell():
        action = broker.Order.Action.SELL
    else:
        raise Exception("Invalid order type")

    ret = broker.LimitOrder(
        action, openOrder.getCurrencyPair(), openOrder.getPrice(), openOrder.getAmount(), instrumentTraits
    )
    ret.setSubmitted(openOrder.getId(), openOrder.getDateTime())
    ret.setState(broker.Order.State.ACCEPTED)
    return ret


class TradeMonitor(threading.Thread):
    POLL_FREQUENCY = 2

    # Events
    ON_USER_TRADE = 1

    def __init__(self, httpClient):
        super(TradeMonitor, self).__init__()
        self.__lastTradeId = -1
        self.__httpClient = httpClient
        self.__queue = queue.Queue()
        self.__stop = False

    def _getNewTrades(self):
        # Retrieve market trade transactions.
        trades = [
            userTransaction for userTransaction in self.__httpClient.getUserTransactions()
            if userTransaction.getType() == httpclient.UserTransaction.Type.MARKET_TRADE
        ]

        # Get the new trades only.
        ret = [t for t in trades if t.getId() > self.__lastTradeId]

        # Sort by id, so older trades first.
        return sorted(ret, key=lambda t: t.getId())

    def getQueue(self):
        return self.__queue

    def start(self):
        trades = self._getNewTrades()
        # Store the last trade id since we'll start processing new ones only.
        if len(trades):
            self.__lastTradeId = trades[-1].getId()
            common.logger.info("Last trade found: %d" % (self.__lastTradeId))

        super(TradeMonitor, self).start()

    def run(self):
        while not self.__stop:
            try:
                trades = self._getNewTrades()
                if len(trades):
                    self.__lastTradeId = trades[-1].getId()
                    common.logger.info("%d new trade/s found" % (len(trades)))
                    self.__queue.put((TradeMonitor.ON_USER_TRADE, trades))
            except Exception as e:
                common.logger.critical("Error retrieving user transactions", exc_info=e)

            time.sleep(TradeMonitor.POLL_FREQUENCY)

    def stop(self):
        self.__stop = True


class LiveBroker(broker.Broker):
    """A Bitstamp live broker.

    :param clientId: Client id.
    :type clientId: string.
    :param key: API key.
    :type key: string.
    :param secret: API secret.
    :type secret: string.


    .. note::
        * Only limit orders are supported.
        * Orders are automatically set as **goodTillCanceled=True** and  **allOrNone=False**.
        * BUY_TO_COVER orders are mapped to BUY orders.
        * SELL_SHORT orders are mapped to SELL orders.
        * API access permissions should include:

          * Account balance
          * Open orders
          * Buy limit order
          * User transactions
          * Cancel order
          * Sell limit order
    """

    QUEUE_TIMEOUT = 0.01

    def __init__(self, clientId, key, secret):
        super(LiveBroker, self).__init__()
        self.__stop = False
        self.__httpClient = self.buildHTTPClient(clientId, key, secret)
        self.__tradeMonitor = TradeMonitor(self.__httpClient)
        self.__balances = {}
        self.__activeOrders = {}

    def _registerOrder(self, order):
        assert(order.getId() not in self.__activeOrders)
        assert(order.getId() is not None)
        self.__activeOrders[order.getId()] = order

    def _unregisterOrder(self, order):
        assert(order.getId() in self.__activeOrders)
        assert(order.getId() is not None)
        del self.__activeOrders[order.getId()]

    # Factory method for testing purposes.
    def buildHTTPClient(self, clientId, key, secret):
        return httpclient.HTTPClient(clientId, key, secret)

    def refreshAccountBalance(self):
        """Refreshes all balances."""

        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Retrieving account balance.")
        account_balance = self.__httpClient.getAccountBalance()

        self.__balances = {}
        for symbol in common.SYMBOL_DIGITS.keys():
            balance = account_balance.getAvailable(symbol)
            common.logger.info("%s %s" % (balance, symbol))
            self.__balances[symbol] = balance

        self.__stop = False  # No errors. Keep running.

    def refreshOpenOrders(self):
        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Retrieving open orders.")
        openOrders = self.__httpClient.getOpenOrders()
        for openOrder in openOrders:
            assert openOrder.getCurrencyPair() in common.SUPPORTED_CURRENCY_PAIRS
            self._registerOrder(build_order_from_open_order(
                openOrder, self.getInstrumentTraits()
            ))

        common.logger.info("%d open order/s found" % (len(openOrders)))
        self.__stop = False  # No errors. Keep running.

    def _startTradeMonitor(self):
        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Initializing trade monitor.")
        self.__tradeMonitor.start()
        self.__stop = False  # No errors. Keep running.

    def _onUserTrades(self, trades):
        for trade in trades:
            order = self.__activeOrders.get(trade.getOrderId())
            if order is not None:
                fee = trade.getFee()

                fillPrice = trade.getBTCUSD()
                btcAmount = trade.getBTC()
                dateTime = trade.getDateTime()

                # Update cash and shares.
                self.refreshAccountBalance()
                # Update the order.
                orderExecutionInfo = broker.OrderExecutionInfo(fillPrice, abs(btcAmount), fee, dateTime)
                order.addExecutionInfo(orderExecutionInfo)
                if not order.isActive():
                    self._unregisterOrder(order)
                # Notify that the order was updated.
                if order.isFilled():
                    eventType = broker.OrderEvent.Type.FILLED
                else:
                    eventType = broker.OrderEvent.Type.PARTIALLY_FILLED
                self.notifyOrderEvent(broker.OrderEvent(order, eventType, orderExecutionInfo))
            else:
                common.logger.info("Trade %d referred to order %d that is not active" % (
                    trade.getId(), trade.getOrderId())
                )

    # BEGIN observer.Subject interface
    def start(self):
        super(LiveBroker, self).start()
        self.refreshAccountBalance()
        self.refreshOpenOrders()
        self._startTradeMonitor()

    def stop(self):
        self.__stop = True
        common.logger.info("Shutting down trade monitor.")
        self.__tradeMonitor.stop()

    def join(self):
        if self.__tradeMonitor.isAlive():
            self.__tradeMonitor.join()

    def eof(self):
        return self.__stop

    def dispatch(self):
        # Switch orders from SUBMITTED to ACCEPTED.
        ordersToProcess = list(self.__activeOrders.values())
        for order in ordersToProcess:
            if order.isSubmitted():
                order.switchState(broker.Order.State.ACCEPTED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.ACCEPTED, None))

        # Dispatch events from the trade monitor.
        try:
            eventType, eventData = self.__tradeMonitor.getQueue().get(True, LiveBroker.QUEUE_TIMEOUT)

            if eventType == TradeMonitor.ON_USER_TRADE:
                self._onUserTrades(eventData)
            else:
                common.logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
        except queue.Empty:
            pass

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # END observer.Subject interface

    # BEGIN broker.Broker interface

    def getBalances(self):
        return copy.copy(self.__balances)

    def getActiveOrders(self, instrument=None):
        return list(self.__activeOrders.values())

    def submitOrder(self, order):
        if order.isInitial():
            assert order.getInstrument() in common.SUPPORTED_CURRENCY_PAIRS

            # Override user settings based on Bitstamp limitations.
            order.setAllOrNone(False)
            order.setGoodTillCanceled(True)

            channelCurrencyPair = common.currency_pair_to_channel(order.getInstrument())
            if order.isBuy():
                bitstampOrder = self.__httpClient.buyLimit(
                    channelCurrencyPair, order.getLimitPrice(), order.getQuantity()
                )
            else:
                bitstampOrder = self.__httpClient.sellLimit(
                    channelCurrencyPair, order.getLimitPrice(), order.getQuantity()
                )

            order.setSubmitted(bitstampOrder.getId(), bitstampOrder.getDateTime())
            self._registerOrder(order)
            # Switch from INITIAL -> SUBMITTED
            # IMPORTANT: Do not emit an event for this switch because when using the position interface
            # the order is not yet mapped to the position and Position.onOrderUpdated will get called.
            order.switchState(broker.Order.State.SUBMITTED)
        else:
            raise Exception("The order was already processed")

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        raise Exception("Market orders are not supported")

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        if instrument not in common.SUPPORTED_CURRENCY_PAIRS:
            raise Exception("Unsupported instrument %s" % instrument)

        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY
        elif action == broker.Order.Action.SELL_SHORT:
            action = broker.Order.Action.SELL

        if action not in [broker.Order.Action.BUY, broker.Order.Action.SELL]:
            raise Exception("Only BUY/SELL orders are supported")

        instrumentTraits = self.getInstrumentTraits()
        limitPrice = round(limitPrice, 2)
        quantity = instrumentTraits.roundBaseQuantity(quantity)
        return broker.LimitOrder(action, instrument, limitPrice, quantity, instrumentTraits)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")

    def cancelOrder(self, order):
        activeOrder = self.__activeOrders.get(order.getId())
        if activeOrder is None:
            raise Exception("The order is not active anymore")
        if activeOrder.isFilled():
            raise Exception("Can't cancel order that has already been filled")

        self.__httpClient.cancelOrder(order.getId())
        self._unregisterOrder(order)
        order.switchState(broker.Order.State.CANCELED)

        # Update cash and shares.
        self.refreshAccountBalance()

        # Notify that the order was canceled.
        self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))

    # END broker.Broker interface
