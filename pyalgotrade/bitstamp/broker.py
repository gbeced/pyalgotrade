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


from pyalgotrade import broker
from pyalgotrade.broker import backtesting
from pyalgotrade.bitstamp import common
from pyalgotrade.bitstamp import livebroker
from pyalgotrade.instrument import build_instrument


LiveBroker = livebroker.LiveBroker

# In a backtesting or paper-trading scenario the BacktestingBroker dispatches events while processing events from the
# BarFeed.
# It is guaranteed to process BarFeed events before the strategy because it connects to BarFeed events before the
# strategy.


class TradeValidatorPredicate(object):
    def __init__(self, instrumentTraits):
        self._instrumentTraits = instrumentTraits

    def isValidTrade(self, action, instrument, limitPrice, quantity):
        # https://www.bitstamp.net/fee-schedule/
        # The minimum order size is 25.00 USD/EUR for USD/EUR-denominated trading pairs,
        # and 0.001 BTC for BTC-denominated trading pairs.

        if instrument not in common.SUPPORTED_INSTRUMENTS:
            return False, "Unsupported pair %s" % instrument

        # Check the instrument amount.
        minimum = common.MINIMUM_TRADE_AMOUNT.get(instrument.symbol, 0)
        if quantity < minimum:
            return False, "%s amount must be >= %s" % (instrument, minimum)

        # Check the price currency amount.
        minimum = common.MINIMUM_TRADE_AMOUNT.get(instrument.priceCurrency, 0)
        if limitPrice and limitPrice * quantity < minimum:
            return False, "%s amount must be >= %s" % (instrument.priceCurrency, minimum)

        return True, None


class BacktestingBroker(backtesting.Broker):
    """
    A Bitstamp backtesting broker.

    :param initialBalances: A dictionary that maps an instrument/currency/etc to the account's starting balance.
    :type initialBalances: dict.
    :param barFeed: The bar feed that will provide the bars.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param fee: The fee percentage for each order. Defaults to 0.5%.
    :type fee: float.
    :param instrumentTraits: Instrument traits.
    :type instrumentTraits: :class:`pyalgotrade.broker.InstrumentTraits`

    .. note::
        * Only limit orders are supported.
        * Orders are automatically set as **goodTillCanceled=True** and **allOrNone=False**.
        * BUY_TO_COVER orders are mapped to BUY orders.
        * SELL_SHORT orders are mapped to SELL orders.
    """

    def __init__(self, initialBalances, barFeed, fee=0.005, instrumentTraits=livebroker.InstrumentTraits()):
        super(BacktestingBroker, self).__init__(
            initialBalances, barFeed, commission=backtesting.TradePercentage(fee), instrumentTraits=instrumentTraits
        )
        self._tradeValidatorPredicate = TradeValidatorPredicate(instrumentTraits)

    def _getPriceForInstrument(self, instrument):
        assert instrument in common.SUPPORTED_INSTRUMENTS, "Unsupported instrument %s" % instrument
        return super(BacktestingBroker, self)._getPriceForInstrument(instrument)

    def _preSubmitCheck(self, order):
        assert order.getType() == broker.Order.Type.LIMIT

        action = order.getAction()
        quantity = order.getQuantity()

        if action == broker.Order.Action.BUY:
            limitPrice = order.getLimitPrice()
            priceCurrency = order.getInstrument().priceCurrency

            # Check that there is enough cash.
            fee = self.getCommission().calculate(order, limitPrice, quantity)
            required = self.getInstrumentTraits().round(limitPrice * quantity + fee, priceCurrency)
            available = self.getBalance(priceCurrency)
            if required > available:
                raise Exception("Not enough %s. %s required. %s available" % (
                    priceCurrency, required, available
                ))
        elif action == broker.Order.Action.SELL:
            instrument = order.getInstrument()
            available = self.getBalance(instrument.symbol)

            # Check that there are enough coins.
            if quantity > available:
                raise Exception("Not enough %s. %s required. %s available" % (
                    instrument.symbol, quantity, available
                ))
        else:
            raise Exception("Only BUY/SELL orders are supported")

    def setTradeValidatorPredicate(self, predicate):
        self._tradeValidatorPredicate = predicate

    def submitOrder(self, order):
        if order.isInitial():
            self._preSubmitCheck(order)
            # Override user settings based on Bitstamp limitations.
            order.setAllOrNone(False)
            order.setGoodTillCanceled(True)
        return super(BacktestingBroker, self).submitOrder(order)

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        raise Exception("Market orders are not supported")

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        instrument = build_instrument(instrument)

        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY
        elif action == broker.Order.Action.SELL_SHORT:
            action = broker.Order.Action.SELL

        validTrade, reason = self._tradeValidatorPredicate.isValidTrade(
            action, instrument, limitPrice, quantity
        )
        if not validTrade:
            raise Exception("Invalid trade: %s" % reason)

        return super(BacktestingBroker, self).createLimitOrder(action, instrument, limitPrice, quantity)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        raise Exception("Stop orders are not supported")

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        raise Exception("Stop limit orders are not supported")


class PaperTradingBroker(BacktestingBroker):
    """A Bitstamp paper trading broker."""

    pass
