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
from pyalgotrade.instrument import build_instrument


logger = pyalgotrade.logger.getLogger("bitstamp")


SUPPORTED_INSTRUMENTS = {
    build_instrument(pair) for pair in [
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
    ]
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


def instrument_to_channel(instrument):
    assert instrument in SUPPORTED_INSTRUMENTS, "Unsupported currency pair %s" % instrument
    return (instrument.symbol + instrument.priceCurrency).lower()


def channel_to_instrument(channel):
    assert len(channel) == 6
    ret = "%s/%s" % (channel[0:3], channel[3:])
    ret = ret.upper()
    ret = build_instrument(ret)
    assert ret in SUPPORTED_INSTRUMENTS, "Invalid channel %s" % channel
    return ret
