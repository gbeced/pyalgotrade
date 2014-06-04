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

import threading
import time

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

    ret = broker.LimitOrder(openOrder.getId(), action, common.btc_symbol, openOrder.getPrice(), openOrder.getAmount(), instrumentTraits)
    ret.setState(broker.Order.State.ACCEPTED)
    ret.setSubmitDateTime(openOrder.getDateTime())
    return ret


class TradeMonitor(threading.Thread):
    POLL_FREQUENCY = 2

    def __init__(self, clientId, key, secret):
        threading.Thread.__init__(self)
        self.__lastTradeId = -1
        self.__httpClient = httpclient.HTTPClient(clientId, key, secret)
        self.__stop = False

    def _getNewTrades(self):
        userTrades = self.__httpClient.getUserTransactions(httpclient.HTTPClient.UserTransactionType.MARKET_TRADE)

        # Get the new trades only.
        ret = []
        for userTrade in userTrades:
            if userTrade.getId() > self.__lastTradeId:
                ret.append(userTrade)
            else:
                break
        # Older trades first.
        ret.reverse()
        return ret

    def start(self):
        common.logger.info("Starting trade monitor.")
        trades = self._getNewTrades()
        # Store the last trade id since we'll start processing new ones only.
        if len(trades):
            self.__lastTradeId = trades[-1].getId()
            common.logger.info("Last trade found: %d" % (self.__lastTradeId))

        threading.Thread.start(self)

    def run(self):
        while not self.__stop:
            try:
                trades = self._getNewTrades()
                if len(trades):
                    self.__lastTradeId = trades[-1].getId()
                    common.logger.info("%d new trade/s found" % (len(trades)))
            except Exception, e:
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
        * API access permissions should include:

          * Account balance
          * Open orders
          * Buy limit order
          * User transactions
          * Cancel order
          * Sell limit order
    """
    def __init__(self, clientId, key, secret):
        broker.Broker.__init__(self)
        self.__stop = False
        self.__httpClient = httpclient.HTTPClient(clientId, key, secret)
        self.__tradeMonitor = TradeMonitor(clientId, key, secret)
        self.__cash = 0
        self.__shares = {}
        self.__activeOrders = {}

    def refreshAccountBalance(self):
        """Refreshes cash and BTC balance."""

        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Retrieving account balance.")
        balance = self.__httpClient.getAccountBalance()

        # Cash
        self.__cash = balance.getUSDAvailable()
        common.logger.info("%s %s" % (self.__cash, "USD"))
        # BTC
        btc = balance.getBTCAvailable()
        self.__shares = {common.btc_symbol: btc}
        common.logger.info("%s BTC" % (btc))

        self.__stop = False  # No errors. Keep running.

    def refreshOpenOrders(self):
        self.__stop = True  # Stop running in case of errors.
        common.logger.info("Retrieving open orders.")
        openOrders = self.__httpClient.getOpenOrders()
        for openOrder in openOrders:
            self.__activeOrders[openOrder.getId()] = build_order_from_open_order(openOrder, self.getInstrumentTraits(common.btc_symbol))

        common.logger.info("%d open order/s found" % (len(openOrders)))
        self.__stop = False  # No errors. Keep running.

    def _startTradeMonitor(self):
        self.__stop = True  # Stop running in case of errors.
        self.__tradeMonitor.start()
        self.__stop = False  # No errors. Keep running.

    # BEGIN observer.Subject interface
    def start(self):
        self.refreshAccountBalance()
        self.refreshOpenOrders()
        self._startTradeMonitor()

    def stop(self):
        self.__stop = True
        self.__tradeMonitor.stop()

    def join(self):
        if self.__tradeMonitor.isAlive():
            self.__tradeMonitor.join()

    def eof(self):
        return self.__stop

    def dispatch(self):
        # TODO: Check trade events from the TradeMonitor.
        pass

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # END observer.Subject interface

    # BEGIN broker.Broker interface

    def getInstrumentTraits(self, instrument):
        return common.BTCTraits()

    def getShares(self, instrument):
        raise NotImplementedError()

    def getPositions(self):
        raise NotImplementedError()

    def getActiveOrders(self, instrument=None):
        return self.__activeOrders.values()

    def submitOrder(self, order):
        raise NotImplementedError()

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        raise Exception("Market orders are not supported")

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        # TODO: Round limitPrice and quantity as in HTTPClient.
        raise NotImplementedError()

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")

    def cancelOrder(self, order):
        self.__httpClient.cancelOrder(order.getId())

        del self.__activeOrders[order.getId()]
        order.switchState(broker.Order.State.CANCELED)
        self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))

    # END broker.Broker interface
