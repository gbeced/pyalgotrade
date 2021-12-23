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
https://github.com/alpacahq/alpaca-trade-api-python/blob/master/examples/historic_async.py

Example usage:
    from pyalgotrade.alpaca.common import make_async_rest_connection
    from pyalgotrade.alpaca.restfeed import get_historic_data

    async_rest = make_async_rest_connection(api_key_id, api_secret_key)
    results = get_historic_data(async_rest, ['AAPL', 'IBM'], '2021-01-01', '2021-01-10, 'QUOTES')


"""


from enum import Enum
import datetime
import os
import sys
import asyncio
import argparse

import pandas as pd

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, URL
from alpaca_trade_api.rest_async import gather_with_concurrency, AsyncRest

from pyalgotrade.alpaca import common
# from pyalgotrade.alpaca import livefeed

# LiveTradeFeed = livefeed.LiveTradeFeed


NY = 'America/New_York'

async def get_historic_data(async_rest, symbols, start_date, end_date,
                            data_type = 'BARS', timeframe = '1Day'):
    """
    Retrieve historic data for multiple symbols using Alpaca's get_[datatype]_async
    from the AsyncRest object.

    Args:
        async_rest (Alpaca AsyncRest object): See alpaca_trade_api.rest_async.AsyncRest.
        symbols (list): A list of symbols for which to get data.
        start_date (str): Start date of time period of data request.
        end_date (str): End date of time period of data request.
        data_type (str, optional): One of 'BARS', 'TRADES', or 'QUOTES'. Defaults to 'BARS'.
        timeframe (str): Frequency of data requested. Format as [amount][unit],
            where [amount]is an integer, and [unit] is one of Min, Hour, or Day. Defaults to 1Day.
            Ignored if data_type is not 'BARS'.

    Returns:
        [(symbol, df),]: List of tuples of (symbol, pandas DataFrame)
    
    Usage:
        async_rest = make_async_rest_connetion()
        symbols, dfs = 

    """
    # Check Python version
    major = sys.version_info.major
    minor = sys.version_info.minor
    if major < 3 or minor < 6:
        raise Exception('asyncio is not support in your python version')
    msg = f"Getting {data_type} data for {len(symbols)} symbols"
    msg += f", timeframe: {timeframe}" if timeframe else ""
    msg += f" between dates: start={start_date}, end={end_date}"
    common.logger.info(msg)

    # define what data we're trying to get
    if data_type.upper() == 'BARS':
        get_data_method = async_rest.get_bars_async
    elif data_type.upper() == 'TRADES':
        get_data_method = async_rest.get_trades_async
    elif data_type.upper() == 'QUOTES':
        get_data_method = async_rest.get_quotes_async
    else:
        raise Exception(f"Unsupoported data type: {data_type}")
    
    # Time period of data request
    start_date = pd.Timestamp(start_date, tz=NY).date().isoformat()
    end_date = pd.Timestamp(end_date, tz=NY).date().isoformat()

    # ignore timeframe argument if data_type is not 'BARS'
    if data_type.upper() != 'BARS':
        timeframe = None

    # Create one task for each symbol
    # execute up to 1000 tasks each loop
    step_size = 1000
    results = []
    for i in range(0, len(symbols), step_size):
        tasks = []
        for symbol in symbols[i:i+step_size]:
            args = [symbol, start_date, end_date, timeframe] if timeframe else \
                [symbol, start_date, end_date]
            tasks.append(get_data_method(*args))

        if minor >= 8:
            results.extend(await asyncio.gather(*tasks, return_exceptions=True))
        else:
            results.extend(await gather_with_concurrency(500, *tasks))
    
    # notify the user of any bad reuests
    bad_requests = 0
    for response in results:
        if isinstance(response, Exception):
            common.logger.error(f"Got an error: {response}")
        elif not len(response[1]):
            bad_requests += 1

    common.logger.info(f"Total of {len(results)} {data_type}, and {bad_requests} "
          f"empty responses.")
    
    return results

if __name__ == '__main__':

    # Get parameters
    parser = argparse.ArgumentParser(description="Alpaca Rest Datafeed")

    # data request
    parser.add_argument("--symbols", required = True, nargs = '+',
                        help = "One or more symbols for which to download data.")
    parser.add_argument("--start-date", required=True,
                        type=str, help="Start date of data.")
    parser.add_argument("--end-date", required=True,
                        type=str, help="End date of data.")
    parser.add_argument("--datatype", required = False, default="bars",
                        choices = ['bars', 'trades', 'quotes'],
                        help="The type of data to request. One of bars, trades, or quotes.")
    parser.add_argument("--timeframe", required = False, default="1Day",
                        help="The frequency of the bars, in format [n]Min, [n]Hour, or [n]Day.")
    # credentials
    parser.add_argument("--api-key-id", required=False,
                        help="Alpaca Key ID if it is not saved as an environment variable.")
    parser.add_argument("--api-secret-key", required=False,
                        help="Alpaca secret key if it is not saved as an environment variable.")
    # storage
    parser.add_argument("--storage", required=True,
                        help="The path were the files will be downloaded to")
    # parser.add_argument("--force-download", action='store_false',
    #                     help="Force downloading even if the files exist")

    # Set up variables
    args = parser.parse_args()

    # make rest connection to API
    async_rest = common.make_async_rest_connection(args.api_key_id, args.api_secret_key)

    # storage
    if not os.path.exists(args.storage):
        common.logger.info("Creating %s directory" % (args.storage))
        os.mkdir(args.storage)
    storage = args.storage

    # rest of data request
    symbols = args.symbols
    start_date = args.start_date
    end_date = args.end_date
    datatype = args.datatype.upper()
    timeframe = args.timeframe

    # Request the data
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(
        get_historic_data(async_rest, symbols, start_date, end_date, datatype, timeframe)
        )

    # Stack the results into 1 dataframe
    # Current it is in [(symbol0, df0), (symbol1, df1)] format
    result = None
    for symbol_i, df_i in results:
        df_i['symbol'] = symbol_i
        df_i = df_i.reset_index().set_index(['symbol', 'timestamp'])
        if result is None:
            result = df_i
        else:
            result = pd.concat([result, df_i], axis = 0, ignore_index = True)

    # save to csv
    result.to_csv(storage)