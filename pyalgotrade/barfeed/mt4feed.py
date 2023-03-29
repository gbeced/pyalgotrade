# PyAlgoTrade
#
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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
.. moduleauthor:: Svintsov Dmitry <root@uralbash.ru>
"""

from pyalgotrade import barfeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar
from pyalgotrade import dataseries

import types
import datetime

######################################################################
# MetaTrader CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Time,Open,High,Low,Close,Volume
#
# The csv Date column must have the following format: YYYY.MM.DD
# Time: HH:MM


class RowParser(csvfeed.RowParser):
    def __init__(self, dailyBarTime, timezone=None):
        self.__dailyBarTime = dailyBarTime
        self.__timezone = timezone

    def __parseDate(self, dateString):
        return datetime.datetime.strptime(dateString, "%Y.%m.%d %H:%M")

    def getFieldNames(self):
        # It is expected for the first row to have the field names.
        return None

    def getDelimiter(self):
        return ","

    def parseBar(self, csvRowDict):
        time = csvRowDict["Time"]
        dateTime = self.__parseDate(csvRowDict["Date"] + " " + time)
        close = float(csvRowDict["Close"])
        open_ = float(csvRowDict["Open"])
        high = float(csvRowDict["High"])
        low = float(csvRowDict["Low"])
        volume = float(csvRowDict["Volume"])
        return bar.BasicBar(dateTime, open_, high, low, close, volume, None)


class Feed(csvfeed.BarFeed):
    """A :class:`pyalgotrade.barfeed.csvfeed.BarFeed` that loads bars from CSV files downloaded from MetaTrader.

    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        If not None, it must be greater than 0.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.

    .. note::
        MetaTrader csv files lack timezone information.
        When working with multiple instruments:

            * If all the instruments loaded are in the same timezone, then the timezone parameter may not be specified.
            * If any of the instruments loaded are from different timezones, then the timezone parameter must be set.
    """

    def __init__(self, timezone=None, maxLen=dataseries.DEFAULT_MAX_LEN):
        if isinstance(timezone, types.IntType):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        csvfeed.BarFeed.__init__(self, barfeed.Frequency.DAY, maxLen)
        self.__timezone = timezone

    def barsHaveAdjClose(self):
        return False

    def addBarsFromCSV(self, instrument, path, timezone=None):
        """Loads bars for a given instrument from a CSV formatted file.
        The instrument gets registered in the bar feed.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param path: The path to the CSV file.
        :type path: string.
        :param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
        :type timezone: A pytz timezone.
        """

        if isinstance(timezone, types.IntType):
            raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if timezone is None:
            timezone = self.__timezone
        rowParser = RowParser(self.getDailyBarTime(), timezone)
        csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser)
