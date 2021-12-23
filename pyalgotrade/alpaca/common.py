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
from enum import Enum
import os

from alpaca_trade_api.rest_async import AsyncRest

import pyalgotrade.logger
from pyalgotrade import broker


logger = pyalgotrade.logger.getLogger("alpaca")


def make_async_rest_connection(api_key_id = None, api_secret_key = None):
    
    # credentials
    api_key_id = api_key_id or os.environ.get('ALPACA_API_KEY_ID')
    api_secret_key = api_secret_key or os.environ.get('ALPACA_API_SECRET_KEY')

    if api_key_id is None:
        logger.error('Unable to retrieve API Key ID.')
    if api_key_id is None:
        logger.error('Unable to retrieve API Secret Key.')
    
    rest = AsyncRest(key_id=api_key_id,
                    secret_key=api_secret_key)
    
    return rest


















# btc_symbol = "BTC"


# class BTCTraits(broker.InstrumentTraits):
#     def roundQuantity(self, quantity):
#         return round(quantity, 8)
