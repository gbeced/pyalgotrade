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
import os
from datetime import datetime

import msgpack
import pandas as pd

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest_async import AsyncRest
from alpaca_trade_api.stream import Stream

import pyalgotrade.logger
from pyalgotrade import broker


logger = pyalgotrade.logger.getLogger("alpaca")

def make_connection(connection_type, api_key_id = None, api_secret_key = None, live = False):
    """Makes a connection to Alpaca.

    https://alpaca.markets/docs/api-documentation/api-v2/

    Args:
        connection_type: The connection to make to Alpaca. One of [rest, async_rest, stream].
        api_key_id (str, optional): If none, looks at the environment variable ALPACA_API_KEY_ID.
            Defaults to None.
        api_secret_key (str, optional): If none, looks at the environment variable ALPACA_API_SECRET_KEY.
            Defaults to None.
    """ 

    # credentials
    if live:
        api_key_id = api_key_id or os.environ.get('ALPACA_API_KEY_ID')
        api_secret_key = api_secret_key or os.environ.get('ALPACA_API_SECRET_KEY')
    else:
        api_key_id = api_key_id or os.environ.get('ALPACA_API_KEY_ID_PAPER')
        api_secret_key = api_secret_key or os.environ.get('ALPACA_API_SECRET_KEY_PAPER')
    
    if api_key_id is None:
        logger.error('Unable to retrieve API Key ID.')
    if api_key_id is None:
        logger.error('Unable to retrieve API Secret Key.')

    if connection_type == 'async_rest':
        connection = AsyncRest(key_id=api_key_id, secret_key=api_secret_key)
    elif connection_type == 'rest':
        connection = tradeapi.REST(key_id = api_key_id, secret_key = api_secret_key)
    elif connection_type == 'stream':
        connection = Stream(data_feed = 'IEX', key_id=api_key_id, secret_key=api_secret_key, raw_data = True)
    
    return connection

def json_serializer(obj):
    if isinstance(obj, datetime):
        return {'_isoformat': obj.isoformat()}
    elif isinstance(obj, msgpack.ext.Timestamp):
        return {'_unix_nano': obj.to_unix_nano()}
    raise TypeError('...')

def json_deserializer(obj):
    if (_isoformat := obj.get('_isoformat')) is not None:
        return datetime.fromisoformat(_isoformat)
    elif (_unix_nano := obj.get('_unix_nano')) is not None:
        return pd.to_datetime(_unix_nano)
    return obj