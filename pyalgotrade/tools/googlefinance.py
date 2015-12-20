# -*- coding: utf-8 -*-
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
.. moduleauthor:: Maciej Żok <maciek.zok@gmail.com>
"""

import os
import datetime

import pyalgotrade.logger
from pyalgotrade import bar
from pyalgotrade.barfeed import googlefeed
from pyalgotrade.utils import csvutils


def download_csv(instrument, begin, end):
    url = "http://www.google.com/finance/historical"
    params = {
        "q": instrument,
        "startdate": begin.strftime("%Y-%m-%d"),
        "enddate": end.strftime("%Y-%m-%d"),
        "output": "csv",
    }

    return csvutils.download_csv(url, url_params=params, content_type="application/vnd.ms-excel")


def download_daily_bars(instrument, year, csvFile):
    """Download daily bars from Google Finance for a given year.

    :param instrument: Instrument identifier.
    :type instrument: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    """

    bars = download_csv(instrument,
                        datetime.date(year, 1, 1),
                        datetime.date(year, 12, 31))
    f = open(csvFile, "w")
    f.write(bars)
    f.close()


def build_feed(instruments, fromYear, toYear, storage, frequency=bar.Frequency.DAY, timezone=None, skipErrors=False):
    """Build and load a :class:`pyalgotrade.barfeed.googlefeed.Feed` using CSV files downloaded from Google Finance.
    CSV files are downloaded if they haven't been downloaded before.

    :param instruments: Instrument identifiers.
    :type instruments: list.
    :param fromYear: The first year.
    :type fromYear: int.
    :param toYear: The last year.
    :type toYear: int.
    :param storage: The path were the files will be loaded from, or downloaded to.
    :type storage: string.
    :param frequency: The frequency of the bars. Only **pyalgotrade.bar.Frequency.DAY** is currently supported.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param skipErrors: True to keep on loading/downloading files in case of errors.
    :type skipErrors: boolean.
    :rtype: :class:`pyalgotrade.barfeed.googlefeed.Feed`.
    """

    logger = pyalgotrade.logger.getLogger("googlefinance")
    ret = googlefeed.Feed(frequency, timezone)

    if not os.path.exists(storage):
        logger.info("Creating {dirname} directory".format(dirname=storage))
        os.mkdir(storage)

    for year in range(fromYear, toYear+1):
        for instrument in instruments:
            fileName = os.path.join(
                storage,
                "{instrument}-{year}-googlefinance.csv".format(
                    instrument=instrument, year=year))
            if not os.path.exists(fileName):
                logger.info(
                    "Downloading {instrument} {year} to {filename}".format(
                        instrument=instrument, year=year, filename=fileName))
                try:
                    if frequency == bar.Frequency.DAY:
                        download_daily_bars(instrument, year, fileName)
                    else:
                        raise Exception("Invalid frequency")
                except Exception, e:
                    if skipErrors:
                        logger.error(str(e))
                        continue
                    else:
                        raise e
            ret.addBarsFromCSV(instrument, fileName)
    return ret
