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
from pyalgotrade import broker


logger = pyalgotrade.logger.getLogger("bitstamp")

# deprecated
btc_symbol = "BTC"

available_fiats = {"EUR", "USD"}
available_cryptos = {"BTC", "ETH", "LTC", "XRP"}
available_pairs = {"EUR": {"BTC": "BTCEUR", "ETH": "ETHEUR", "LTC": "LTCEUR", "USD": "EURUSD", "XRP": "XRPEUR"},
                   "USD": {"BTC": "BTCUSD", "ETH": "ETHUSD", "EUR": "EURUSD", "LTC": "LTCUSD", "XRP": "XRPUSD"},
                   "BTC": {"EUR": "BTCEUR", "USD": "BTCUSD", "ETH": "ETHBTC", "LTC": "LTCBTC", "XRP": "XRPBTC"},
                   "ETH": {"EUR": "ETHEUR", "USD": "ETHUSD", "BTC": "ETHBTC"},
                   "XRP": {"EUR": "XRPEUR", "USD": "XRPUSD", "BTC": "XRPBTC"},
                   "LTC": {"EUR": "LTCEUR", "USD": "LTCUSD", "BTC": "LTCBTC"}}

class BTCTraits(broker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return round(quantity, 8)
