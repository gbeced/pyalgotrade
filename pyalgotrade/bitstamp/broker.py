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

from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade.bitstamp import client
import pyalgotrade.logger


btc_symbol = "BTC"
logger = pyalgotrade.logger.getLogger("bitstamp")


class BTCTraits(broker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return round(quantity, 8)


# In a backtesting or paper-trading scenario the BacktestingBroker dispatches events while processing events from the BarFeed.
# It is guaranteed to process BarFeed events before the strategy because it connects to BarFeed events before the strategy.

class BacktestingBroker(backtesting.Broker):
    """A Bitstamp backtesting broker.

    :param cash: The initial amount of cash.
    :type cash: int/float.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param fee: The fee percentage for each order. Defaults to 0.5%.
    :type fee: float.

    .. note::
        Only limit orders are supported.
    """

    def __init__(self, cash, barFeed, fee=0.005):
        commission = backtesting.TradePercentage(fee)
        backtesting.Broker.__init__(self, cash, barFeed, commission)

    def getInstrumentTraits(self, instrument):
        return BTCTraits()

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        raise Exception("Market orders are not supported")

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        if action not in [broker.Order.Action.BUY, broker.Order.Action.SELL]:
            raise Exception("Only BUY/SELL orders are supported")
        if instrument != btc_symbol:
            raise Exception("Only BTC instrument is supported")
        return backtesting.Broker.createLimitOrder(self, action, instrument, limitPrice, quantity)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")


class PaperTradingBroker(BacktestingBroker):
    """A Bitstamp paper trading broker.

    :param cash: The initial amount of cash.
    :type cash: int/float.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param fee: The fee percentage for each order. Defaults to 0.5%.
    :type fee: float.

    .. note::
        Only limit orders are supported.
    """

    pass


class LiveBroker(broker.Broker):
    """A Bitstamp live broker.

    :param cli: A bitstamp client.
    :type cli: :class:`pyalgotrade.bitstamp.client.Client`.
    :param clientId: Client id.
    :type clientId: string.
    :param key: API key.
    :type key: string.
    :param secret: API secret.
    :type secret: string.


    .. note::
        Only limit orders are supported.
    """
    def __init__(self, cli, clientId, key, secret):
        broker.Broker.__init__(self)
        self.__stop = False
        self.__httpClient = client.HTTPClient(clientId, key, secret)
        self.__cash = 0
        self.__shares = {}

    def refreshAccountBalance(self):
        self.__stop = True  # Stop running in case of errors.
        logger.info("Retrieving account balance.")
        balance = self.__httpClient.getAccountBalance()

        # Cash
        self.__cash = balance.getUSDAvailable()
        logger.info("%s %s" % (self.__cash, "USD"))
        # BTC
        btc = balance.getBTCAvailable()
        self.__shares = {btc_symbol: btc}
        logger.info("%s BTC" % (btc))

        self.__stop = False  # No errors. Keep running.

    def refreshOpenOrders(self):
        self.__stop = True  # Stop running in case of errors.
        logger.info("Retrieving open orders.")
        self.__stop = False  # No errors. Keep running.

    # BEGIN observer.Subject interface
    def start(self):
        self.refreshAccountBalance()
        self.refreshOpenOrders()

    def stop(self):
        self.__stop = True

    def join(self):
        pass

    def eof(self):
        return self.__stop

    def dispatch(self):
        # TODO: Dispatch order events when they come from the feed.
        pass

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # END observer.Subject interface

    # BEGIN broker.Broker interface

    def getInstrumentTraits(self, instrument):
        return BTCTraits()

    def getShares(self, instrument):
        raise NotImplementedError()

    def getPositions(self):
        raise NotImplementedError()

    def getActiveOrders(self, instrument=None):
        raise NotImplementedError()

    def submitOrder(self, order):
        raise NotImplementedError()

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        raise Exception("Market orders are not supported")

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        raise NotImplementedError()

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")

    def cancelOrder(self, order):
        raise NotImplementedError()

    # END broker.Broker interface
