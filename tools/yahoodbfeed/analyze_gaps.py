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

import sys
import os
import datetime

sys.path.append(os.path.join("..", "symbols"))
sys.path.append(os.path.join("..", ".."))  # For pyalgotrade

import symbolsxml
import merval_calendar
import pyalgotrade.logger

pyalgotrade.logger.file_log = "analyze_gaps.log"
logger = pyalgotrade.logger.getLogger("analyze_gaps")

from pyalgotrade.barfeed import yahoofeed


storage = "data"


class MissingDataVerifier:
    def __init__(self, barDataSeries, threshold):
        self.__barDataSeries = barDataSeries
        self.__threshold = threshold

    def isTradingDay(self, dateTime):
        raise NotImplementedError()

    def getDatesInBetween(self, prevDateTime, currentDateTime):
        assert((currentDateTime - prevDateTime).days > 1)
        ret = []
        dateTime = prevDateTime + datetime.timedelta(days=1)
        while dateTime < currentDateTime:
            # Skip weekends.
            if dateTime.weekday() not in [5, 6]:
                ret.append(dateTime.date())
            dateTime = dateTime + datetime.timedelta(days=1)
        return ret

    def __processGap(self, prevDateTime, currentDateTime):
        dates = self.getDatesInBetween(prevDateTime, currentDateTime)
        dates = filter(lambda x: not self.isTradingDay(x), dates)
        if len(dates) >= self.__threshold:
            logger.warning("%d day gap between %s and %s" % (len(dates), prevDateTime, currentDateTime))

    def run(self):
        prevDateTime = None
        for bar in self.__barDataSeries:
            currentDateTime = bar.getDateTime()
            if prevDateTime is not None:
                if (currentDateTime - prevDateTime).days > 1:
                    self.__processGap(prevDateTime, currentDateTime)
            prevDateTime = currentDateTime


def get_csv_filename(symbol, year):
    return os.path.join(storage, "%s-%d-yahoofinance.csv" % (symbol, year))


def process_symbol(symbol, fromYear, toYear, missingDataVerifierClass):
    logger.info("Processing %s from %d to %d" % (symbol, fromYear, toYear))

    filesFound = 0
    # Load the bars from the CSV files.
    feed = yahoofeed.Feed(maxLen=1000000)
    feed.sanitizeBars(True)
    for year in range(fromYear, toYear+1):
        fileName = get_csv_filename(symbol, year)
        if os.path.exists(fileName):
            filesFound += 1
            feed.addBarsFromCSV(symbol, fileName)

    if filesFound > 0:
        # Process all items.
        for dateTime, bars in feed:
            pass

        missingDataVerifier = missingDataVerifierClass(feed[symbol])
        missingDataVerifier.run()
    else:
        logger.error("No files found")


class MervalMissingDataVerifier(MissingDataVerifier):
    def __init__(self, barDataSeries):
        MissingDataVerifier.__init__(self, barDataSeries, 5)

    def isTradingDay(self, dateTime):
        return not merval_calendar.is_trading_day(dateTime)


def main():
    fromYear = 2000
    toYear = 2012

    try:
        # MERVAL config.
        symbolsFile = os.path.join("..", "symbols", "merval.xml")
        missingDataVerifierClass = MervalMissingDataVerifier

        stockCallback = lambda stock: process_symbol(stock.getTicker(), fromYear, toYear, missingDataVerifierClass)
        indexCallback = stockCallback
        symbolsxml.parse(symbolsFile, stockCallback, indexCallback)
    except Exception, e:
        logger.error(str(e))

main()
