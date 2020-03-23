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

import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger("bitstamp")


SUPPORTED_CURRENCY_PAIRS = {
    "BCH/BTC",
    "BCH/EUR",
    "BCH/USD",
    "BTC/EUR",
    "BTC/USD",
    "ETH/BTC",
    "ETH/EUR",
    "ETH/USD",
    "EUR/USD",
    "LTC/BTC",
    "LTC/EUR",
    "LTC/USD",
    "XRP/BTC",
    "XRP/EUR",
    "XRP/USD",
}


SYMBOL_DIGITS = {
    # Fiat currencies
    "EUR": 2,
    "USD": 2,
    # Crypto currencies.
    "BCH": 8,
    "BTC": 8,
    "ETH": 18,
    "LTC": 8,
    "XRP": 6,
}


MINIMUM_TRADE_AMOUNT = {
    "BTC": 0.001,
    "EUR": 25,
    "USD": 25,
}


def currency_pair_to_channel(currencyPair):
    assert currencyPair in SUPPORTED_CURRENCY_PAIRS, "Unsupported currency pair %s" % currencyPair
    return currencyPair.replace("/", "").lower()


def channel_to_currency_pair(channel):
    assert len(channel) == 6
    ret = "%s/%s" % (channel[0:3], channel[3:])
    ret = ret.upper()
    assert ret in SUPPORTED_CURRENCY_PAIRS, "Invalid channel %s" % channel
    return ret
