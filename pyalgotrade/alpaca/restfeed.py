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

class DataType(str, Enum):
    Bars = "Bars"
    Trades = "Trades"
    Quotes = "Quotes"


def get_data_method(data_type: DataType):
    if data_type == DataType.Bars:
        return rest.get_bars_async
    elif data_type == DataType.Trades:
        return rest.get_trades_async
    elif data_type == DataType.Quotes:
        return rest.get_quotes_async
    else:
        raise Exception(f"Unsupoported data type: {data_type}")


async def get_historic_data_base(symbols, data_type: DataType, start, end,
                                 timeframe: TimeFrame = None):
    """
    base function to use with all
    :param symbols:
    :param start:
    :param end:
    :param timeframe:
    :return:
    """
    # Check Python version
    major = sys.version_info.major
    minor = sys.version_info.minor
    if major < 3 or minor < 6:
        raise Exception('asyncio is not support in your python version')
    msg = f"Getting {data_type} data for {len(symbols)} symbols"
    msg += f", timeframe: {timeframe}" if timeframe else ""
    msg += f" between dates: start={start}, end={end}"
    common.logger.info(msg)

    # loop through 1000 symbols at a time
    step_size = 1000
    results = []
    for i in range(0, len(symbols), step_size):
        tasks = []
        for symbol in symbols[i:i+step_size]:
            args = [symbol, start, end, timeframe.value] if timeframe else \
                [symbol, start, end]
            tasks.append(get_data_method(data_type)(*args))

        if minor >= 8:
            results.extend(await asyncio.gather(*tasks, return_exceptions=True))
        else:
            results.extend(await gather_with_concurrency(500, *tasks))

    bad_requests = 0
    for response in results:
        if isinstance(response, Exception):
            common.logger.error(f"Got an error: {response}")
        elif not len(response[1]):
            bad_requests += 1

    common.logger.info(f"Total of {len(results)} {data_type}, and {bad_requests} "
          f"empty responses.")
    
    return results


# async def get_historic_bars(symbols, start, end, timeframe: TimeFrame):
#     await get_historic_data_base(symbols, DataType.Bars, start, end, timeframe)


# async def get_historic_trades(symbols, start, end, timeframe: TimeFrame):
#     await get_historic_data_base(symbols, DataType.Trades, start, end)


# async def get_historic_quotes(symbols, start, end, timeframe: TimeFrame):
#     await get_historic_data_base(symbols, DataType.Quotes, start, end)


# async def main(symbols, start_time, end_time, timeframe):
#     start = pd.Timestamp(start_time, tz=NY).date().isoformat()
#     end = pd.Timestamp(end_time, tz=NY).date().isoformat()



#     # await get_historic_bars(symbols, start, end, timeframe)
#     # await get_historic_trades(symbols, start, end, timeframe)
#     # await get_historic_quotes(symbols, start, end, timeframe)


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

    # credentials
    api_key_id = args.api_key_id or os.environ.get('ALPACA_API_KEY_ID')
    api_secret_key = args.api_secret_key or os.environ.get('ALPACA_API_SECRET_KEY')
    # data request
    symbols = args.symbols
    start_date = pd.Timestamp(args.start_date, tz=NY).date().isoformat()
    end_date = pd.Timestamp(args.end_date, tz=NY).date().isoformat()
    if args.datatype == 'bars':
        datatype = DataType.Bars
    elif args.datatype == 'trades':
        datatype = DataType.Trades
    elif args.datatype == 'quotes':
        datatype = DataType.Quotes
    timeframe = args.timeframe
    # storage
    if not os.path.exists(args.storage):
        common.logger.info("Creating %s directory" % (args.storage))
        os.mkdir(args.storage)
    storage = args.storage

    
    # Make connection
    base_url = "https://paper-api.alpaca.markets"
    rest = AsyncRest(key_id=api_key_id,
                     secret_key=api_secret_key)
    feed = "sip"  # change to "iex" if only free account

    api = tradeapi.REST(key_id=api_key_id,
                        secret_key=api_secret_key,
                        base_url=URL(base_url))
    
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(
        get_historic_data_base(symbols, datatype, start_date, end_date, timeframe)
        )
    # f = open(storage, "w")
    # f.write(bars)
    # f.close()



# TODO
# split out function for non-command line use
# test functions