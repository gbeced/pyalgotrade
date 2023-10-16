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
.. moduleauthor:: Dark Shadow <techpranav@gmail.com>
"""

import os
from datetime import date

import pandas as pd
import six
from nsedt import equity as eq

import pyalgotrade.logger
from pyalgotrade import bar
from pyalgotrade.barfeed import nsedtfeed
from pyalgotrade.constants import Constants
from pyalgotrade.utils.Utils import getNSEFileName


# https://github.com/gbeced/pyalgotrade/tree/master


def exportToExcel(symbol, export_dict, filename, storage=Constants.SAMPLE_DATA_DIR):
    if filename is None:
        filename = symbol + '.xlsx'
    filename = os.path.join(storage, filename)
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        for sheetName in export_dict:
            df = export_dict[sheetName]
            df.to_excel(writer, sheet_name=sheetName, index=True)

    return filename


def fetchSymbolData(symbol: str, startdate: date, enddate: date, export_corpinfo: bool = False,
                    export_events: bool = False, export_marketstatus: bool = False, export_companyinfo: bool = False,
                    export_chartdata: bool = False, export_price: bool = True) -> object:
    global start_date, end_date
    export_dict = {}
    if export_price:
        price = eq.get_price(startdate, enddate, symbol=symbol)
        price = price.drop_duplicates(subset='Date')
        export_dict["price"] = price

    start_date = startdate.strftime("%d-%m-%Y")
    end_date = enddate.strftime("%d-%m-%Y")
    if export_corpinfo:
        export_dict["corpInfo"] = eq.get_corpinfo(start_date, end_date, symbol=symbol)
    if export_events:
        export_dict["events"] = eq.get_event(start_date, end_date);
    if export_marketstatus:
        export_dict["MarketStatus"] = eq.get_marketstatus()
        print(eq.get_marketstatus(response_type="json"))
    if export_companyinfo:
        export_dict["companyInfo"] = eq.get_companyinfo(symbol=symbol)
        print(eq.get_companyinfo(symbol=symbol, response_type="json"))
    if export_chartdata:
        export_dict["chartData"] = eq.get_chartdata(symbol=symbol)
    return export_dict


def download_excel(symbol: str, startdate: date, enddate: date, filename=None, storage=Constants.SAMPLE_DATA_DIR,
                   export_corpinfo: bool = False, export_events: bool = False, export_marketstatus: bool = False,
                   export_companyinfo: bool = False, export_chartdata: bool = False, export_price: bool = True):
    if filename is None:
        filename = getNSEFileName(symbol, startdate, enddate) + ".xlsx"
    if os.path.exists(os.path.join(storage, filename)):
        return os.path.join(storage, filename)
    export_dict = fetchSymbolData(symbol, startdate, enddate, export_corpinfo, export_events, export_marketstatus,
                                  export_companyinfo, export_chartdata, export_price)
    return exportToExcel(symbol, export_dict, storage=storage, filename=filename)


def download_csv(symbol: str, startdate: date, enddate: date, filename=None, storage=Constants.SAMPLE_DATA_DIR):
    if filename is None:
        filename = getNSEFileName(symbol, startdate, enddate) + '.csv'

    if os.path.exists(os.path.join(storage, filename)):
        return os.path.join(storage, filename)
    export_dict = fetchSymbolData(symbol, startdate, enddate)
    df = export_dict["price"]
    filename = os.path.join(storage, filename)

    df.to_csv(filename, index=False)
    return filename


def build_feed(symbols, startdate: date, enddate: date, filename=None, storage=Constants.SAMPLE_DATA_DIR,
               columnNames={}, export_corpinfo: bool = False, export_events: bool = False,
               export_marketstatus: bool = False, export_companyinfo: bool = False, export_chartdata: bool = False,
               export_price: bool = True, skipErrors=False, exportToCSV=True, skipMalformedBars=False):
    """Build and load a :class:`pyalgotrade.barfeed.nsedtfee.Feed` using CSV files downloaded from NseDT.
    CSV files are downloaded if they haven't been downloaded before.

    :param sourceCode: The dataset source code.
    :type sourceCode: string.
    :param tableCodes: The dataset table codes.
    :type tableCodes: list.
    :param fromYear: The first year.
    :type fromYear: int.
    :param toYear: The last year.
    :type toYear: int.
    :param storage: The path were the files will be loaded from, or downloaded to.
    :type storage: string.
    :param frequency: The frequency of the bars. Only **pyalgotrade.bar.Frequency.DAY** or
                      **pyalgotrade.bar.Frequency.WEEK** are supported.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param skipErrors: True to keep on loading/downloading files in case of errors.
    :type skipErrors: boolean.
    :param authToken: Optional. An authentication token needed if you're doing more than 50 calls per day.
    :type authToken: string.
    :param columnNames: Optional. A dictionary to map column names. Valid key values are:

        * datetime
        * open
        * high
        * low
        * close
        * volume
        * adj_close

    :type columnNames: dict.
    :param skipMalformedBars: True to skip errors while parsing bars.
    :type skipMalformedBars: boolean.

    :rtype: :class:`pyalgotrade.barfeed.quandlfeed.Feed`.
    """

    logger = pyalgotrade.logger.getLogger("NseDT")
    ret = nsedtfeed.Feed(bar.Frequency.DAY, None)

    # Additional column names.
    for col, name in six.iteritems(columnNames):
        ret.setColumnName(col, name)

    if not os.path.exists(storage):
        logger.info("Creating %s directory" % (storage))
        os.mkdir(storage)

    for tableCode in symbols:
        try:
            if exportToCSV:
                print("Downloading CSV")
                filename = download_csv(symbol=tableCode, startdate=startdate, enddate=enddate, filename=filename)
            else:
                print("Downloading XLSX")
                filename = download_excel(symbol=tableCode, startdate=startdate, enddate=enddate, filename=filename,
                                          export_price=export_price, export_chartdata=export_chartdata,
                                          export_corpinfo=export_corpinfo, export_companyinfo=export_companyinfo,
                                          export_marketstatus=export_marketstatus, export_events=export_events)
        except Exception as e:
            if skipErrors:
                logger.error(str(e))
                continue
            else:
                raise e
    ret.addBarsFromCSV(tableCode, filename, skipMalformedBars=skipMalformedBars)
    return ret


def main():
    logger = pyalgotrade.logger.getLogger("NseDT")
    symbols = {"DIXON"}
    try:

        start_date = date(year=2011, month=1, day=1)
        end_date = date(year=2023, month=8, day=31)
        for symbol in symbols:
            storage = os.path.join(os.getcwd(), "..", "..", "samples", "data")
            download_excel(symbol=symbol, startdate=start_date, enddate=end_date, storage=storage)
            download_csv(symbol=symbol, startdate=start_date, enddate=end_date, storage=storage)

    except Exception as e:
        raise


def getRootDirectory():
    # Specify the name of the known file at the root
    root_marker = "setup.py"
    # Get the script's directory
    script_directory = os.path.dirname(__file__)
    # Traverse up the directory tree to find the root directory
    root_directory = script_directory
    while root_directory != '/' and root_marker not in os.listdir(root_directory):
        root_directory = os.path.dirname(root_directory)
    print("Project Root Directory:", root_directory)


SAMPLE_DATA_DIRECTORY = getRootDirectory()

if __name__ == "__main__":
    main()
