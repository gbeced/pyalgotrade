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

from pyalgotrade import barfeed
from pyalgotrade import bar
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.utils import dt

import datetime


def to_utc_if_naive(dateTime):
    if dateTime is not None and dt.datetime_is_naive(dateTime):
        dateTime = dt.as_utc(dateTime)
    return dateTime


class TradeBar(bar.Bar):
    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__price', '__amount')

    def __init__(self, dateTime, price, amount):
        self.__dateTime = dateTime
        self.__price = price
        self.__amount = amount

    def __setstate__(self, state):
        (self.__dateTime, self.__price, self.__amount) = state

    def __getstate__(self):
        return (self.__dateTime, self.__price, self.__amount)

    def setUseAdjustedValue(self, useAdjusted):
        if useAdjusted:
            raise Exception("Adjusted close is not available")

    def getUseAdjValue(self):
        return False

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        return self.__price

    def getHigh(self, adjusted=False):
        return self.__price

    def getLow(self, adjusted=False):
        return self.__price

    def getClose(self, adjusted=False):
        return self.__price

    def getVolume(self):
        return self.__amount

    def getAdjClose(self):
        return None

    def getFrequency(self):
        return bar.Frequency.TRADE

    def getPrice(self):
        return self.__price


# As described in http://www.bitcoincharts.com/about/markets-api/
# unixtime has second precision so more than 1 trade in a second will trigger
# duplicate bars checks.
class UnixTimeFix(object):
    def __init__(self):
        self.__lastDateTime = None
        self.__nextFix = 1

    def fixDateTime(self, dateTime):
        ret = dateTime
        if dateTime == self.__lastDateTime:
            ret = dateTime + datetime.timedelta(microseconds=self.__nextFix)
            self.__nextFix += 1
        else:
            # Reset self.__nextFix
            self.__nextFix = 1
        self.__lastDateTime = dateTime
        return ret


class RowParser(csvfeed.RowParser):
    def __init__(self, unixTimeFix, timezone=None):
        self.__unixTimeFix = unixTimeFix
        self.__timezone = timezone

    def parseBar(self, csvRowDict):
        unixTime = int(csvRowDict["unixtime"])
        price = float(csvRowDict["price"])
        amount = float(csvRowDict["amount"])

        dateTime = dt.timestamp_to_datetime(unixTime)
        dateTime = self.__unixTimeFix.fixDateTime(dateTime)

        # Localize the datetime if a timezone was given.
        if self.__timezone:
            dateTime = dt.localize(dateTime, self.__timezone)

        return TradeBar(dateTime, price, amount)

    def getFieldNames(self):
        return ["unixtime", "price", "amount"]

    def getDelimiter(self):
        return ","


class CSVTradeFeed(csvfeed.BarFeed):
    """A BarFeed that builds bars from a Historic Trade Data CSV file as described in http://www.bitcoincharts.com/about/markets-api/.
    Files can be downloaded from http://api.bitcoincharts.com/v1/csv/.

    :param timezone: An optional default timezone to use to localize bars. By default bars are loaded in UTC.
    :type timezone: A pytz timezone.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        If not None, it must be greater than 0.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.

    .. note::
        * A :class:`pyalgotrade.bar.Bar` instance will be created for every trade, so open, high, low and close values will all be the same.
        * Files must be sorted with the **unixtime** column in ascending order.
    """

    def __init__(self, timezone=None, maxLen=None):
        super(CSVTradeFeed, self).__init__(barfeed.Frequency.TRADE, maxLen)
        self.__timezone = timezone
        self.__unixTimeFix = UnixTimeFix()

    def barsHaveAdjClose(self):
        return False

    def addBarsFromCSV(self, path, instrument="BTC", timezone=None, fromDateTime=None, toDateTime=None):
        """Loads bars from a trades CSV formatted file.

        :param path: The path to the file.
        :type path: string.
        :param instrument: The instrument identifier.
        :type instrument: string.
        :param timezone: An optional timezone to use to localize bars. By default bars are loaded in UTC.
        :type timezone: A pytz timezone.
        :param fromDateTime: An optional datetime to use to filter bars to load.
            If supplied only those bars whose datetime is greater than or equal to fromDateTime are loaded.
        :type fromDateTime: datetime.datetime.
        :param toDateTime: An optional datetime to use to filter bars to load.
            If supplied only those bars whose datetime is lower than or equal to toDateTime are loaded.
        :type toDateTime: datetime.datetime.

        .. note::
            * Every file that you load bars from must have trades in the same currency.
            * If fromDateTime or toDateTime are naive, they are treated as UTC.
        """

        if timezone is None:
            timezone = self.__timezone
        rowParser = RowParser(self.__unixTimeFix, timezone)

        # Save the barfilter to restore it later.
        prevBarFilter = self.getBarFilter()
        try:
            if fromDateTime or toDateTime:
                self.setBarFilter(csvfeed.DateRangeFilter(to_utc_if_naive(fromDateTime), to_utc_if_naive(toDateTime)))
            super(CSVTradeFeed, self).addBarsFromCSV(instrument, path, rowParser)
        finally:
            self.setBarFilter(prevBarFilter)
