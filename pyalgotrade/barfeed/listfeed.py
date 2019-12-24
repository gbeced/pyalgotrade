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
.. moduleauthor:: Alex McFarlane <alexander.mcfarlane@physics.org>, Tyler Kontra <tyler@tylerkontra.com>
"""

from pyalgotrade.utils import dt
from pyalgotrade.barfeed import membf
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar

import datetime


class BarFeed(membf.BarFeed):
    """Base class for Iterable[Dict] based :class:`pyalgotrade.barfeed.BarFeed`.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, frequency, maxLen=None):
        super(BarFeed, self).__init__(frequency, maxLen)

        self.__barFilter = None
        self.__dailyTime = datetime.time(0, 0, 0)

    def getDailyBarTime(self):
        return self.__dailyTime

    def setDailyBarTime(self, time):
        self.__dailyTime = time

    def getBarFilter(self):
        return self.__barFilter

    def setBarFilter(self, barFilter):
        self.__barFilter = barFilter

    def _addBarsFromListofDicts(self, instrument, iterable, rowParser):
        loadedBars = map(rowParser.parseBar, iterable)
        loadedBars = filter(
            lambda bar_: (bar_ is not None) and
                (self.__barFilter is None or self.__barFilter.includeBar(bar_)),
            loadedBars
        )
        self.addBarsFromSequence(instrument, loadedBars)


class Feed(BarFeed):
    """A BarFeed that loads bars from a custom feed that has the following columns:
    ::

                  Date Time     Open    Close     High      Low    Volume  Adj Close
        2015-08-14 09:06:00  0.00690  0.00690  0.00690  0.00690  1.346117       9567
    

    :param frequency: The frequency of the bars. Check :class:`pyalgotrade.bar.Frequency`.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.

    .. note::
        * The data should be sampled across regular time points, you can
            regularlise (e.g. for 5min intervals) as::

                df = df.set_index('Date Time').resample('s').interpolate().resample('5T').asfreq()
                df = df.dropna().reset_index()
            which is described in a SO [post](https://stackoverflow.com/a/39730730/4013571)
        * It is ok if the **Adj Close** column is empty.
        * When working with multiple instruments:

         * If all the instruments loaded are in the same timezone, then the timezone parameter may not be specified.
         * If any of the instruments loaded are in different timezones, then the timezone parameter should be set.
    """

    def __init__(self, frequency, timezone=None, maxLen=None):
        super(Feed, self).__init__(frequency, maxLen)

        self.__timezone = timezone
        # Assume bars don't have adjusted close. This will be set to True after
        # loading the first file if the adj_close column is there.
        self.__haveAdjClose = False

        self.__barClass = bar.BasicBar

        self.__dateTimeFormat = "%Y-%m-%d %H:%M:%S"
        self.__columnNames = {
            "datetime": "Date Time",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "adj_close": "Adj Close",
        }
        # self.__dateTimeFormat expects time to be set so there is no need to
        # fix time.
        self.setDailyBarTime(None)

    def barsHaveAdjClose(self):
        return self.__haveAdjClose

    def setNoAdjClose(self):
        self.__columnNames["adj_close"] = None
        self.__haveAdjClose = False

    def setColumnName(self, col, name):
        self.__columnNames[col] = name

    def setDateTimeFormat(self, dateTimeFormat):
        self.__dateTimeFormat = dateTimeFormat

    def setBarClass(self, barClass):
        self.__barClass = barClass
        
    def addBarsFromListofDicts(self, instrument, list_of_dicts, timezone=None):
        """Loads bars for a given instrument from a list of dictionaries.
        The instrument gets registered in the bar feed.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param list_of_dicts: A list of dicts. First item should contain
            columns.
        :type list_of_dicts: list
        :param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
        :type timezone: A pytz timezone.
        """

        if timezone is None:
            timezone = self.__timezones

        if not isinstance(list_of_dicts, (list, tuple)):
            raise ValueError('This function only supports types: {list, tuple}')
        if not isinstance(list_of_dicts[0], dict):
            raise ValueError('List should only contain dicts')

        rowParser = csvfeed.GenericRowParser(
            self.__columnNames,
            self.__dateTimeFormat,
            self.getDailyBarTime(),
            self.getFrequency(),
            timezone,
            self.__barClass
        )

        missing_columns = [
            col for col in self.__columnNames.values()
            if col not in list_of_dicts[0].keys()
        ]
        if missing_columns:
            raise ValueError('Missing required columns: {}'.format(repr(missing_columns)))

        super(Feed, self)._addBarsFromListofDicts(
            instrument, list_of_dicts, rowParser)

        if rowParser.barsHaveAdjClose():
            self.__haveAdjClose = True
        elif self.__haveAdjClose:
            raise Exception("Previous bars had adjusted close and these ones don't have.")