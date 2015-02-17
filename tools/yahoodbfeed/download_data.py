# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import os
import sys

sys.path.append(os.path.join("..", "symbols"))
sys.path.append(os.path.join("..", ".."))  # For pyalgotrade

import pyalgotrade.logger

pyalgotrade.logger.file_log = "download_data.log"
logger = pyalgotrade.logger.getLogger("download_data")

from pyalgotrade.tools import yahoofinance
import symbolsxml


storage = "data"


def get_csv_filename(symbol, year):
    return os.path.join(storage, "%s-%d-yahoofinance.csv" % (symbol, year))


def download_files_for_symbol(symbol, fromYear, toYear):
    if not os.path.exists(storage):
        logger.info("Creating %s directory" % (storage))
        os.mkdir(storage)

    status = ""
    for year in range(fromYear, toYear+1):
        fileName = get_csv_filename(symbol, year)
        if not os.path.exists(fileName):
            logger.info("Downloading %s %d to %s" % (symbol, year, fileName))
            try:
                yahoofinance.download_daily_bars(symbol, year, fileName)
                status += "1"
            except Exception, e:
                logger.error(str(e))
                status += "0"
        else:
            status += "1"

    if status.find("1") == -1:
        logger.fatal("No data found for %s" % (symbol))
    elif status.lstrip("0").find("0") != -1:
        logger.fatal("Some bars are missing for %s" % (symbol))


def main():
    fromYear = 2000
    toYear = 2013

    try:
        symbolsFile = os.path.join("..", "symbols", "merval.xml")
        callback = lambda stock: download_files_for_symbol(stock.getTicker(), fromYear, toYear)
        symbolsxml.parse(symbolsFile, callback, callback)
    except Exception, e:
        logger.error(str(e))

main()
