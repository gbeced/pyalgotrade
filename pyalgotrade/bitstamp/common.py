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

import six

import pyalgotrade.logger
from pyalgotrade import broker


logger = pyalgotrade.logger.getLogger("bitstamp")


# SUPPORTED_FIAT_CURRENCIES = ["USD", "EUR"]
SUPPORTED_FIAT_CURRENCIES = ["USD"]
# SUPPORTED_CRYPTO_CURRENCIES = ["BTC", "XRP", "LTC", "ETH", "BCH"]
SUPPORTED_CRYPTO_CURRENCIES = ["BTC"]


CURRENCY_PAIR_TO_CHANNEL = {
    "BTC/USD": "btcusd",
}
CHANNEL_TO_CURRENCY_PAIR = {v: k for k, v in six.iteritems(CURRENCY_PAIR_TO_CHANNEL)}

BTC_SYMBOL = "BTC"
USD_SYMBOL = "USD"
BTC_USD_CURRENCY_PAIR = "BTC/USD"
BTC_USD_CHANNEL = CURRENCY_PAIR_TO_CHANNEL[BTC_USD_CURRENCY_PAIR]
SUPPORTED_CURRENCY_PAIRS = set(CURRENCY_PAIR_TO_CHANNEL.keys())


class BTCTraits(broker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return round(quantity, 8)


def split_currency_pair(currencyPair):
    """Splits a currency pair into base currency and quote currency"""
    assert len(currencyPair) == 7, "Invalid currency pair"
    assert currencyPair[3] == "/", "Invalid currency pair"

    return currencyPair[:3], currencyPair[4:]
