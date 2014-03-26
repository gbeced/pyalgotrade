# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import abc
import datetime

from pyalgotrade.utils import dt
from pyalgotrade.utils import csvutils
from pyalgotrade.feed import memfeed
from pyalgotrade import dataseries


# Interface for csv row parsers.
class RowParser(object):

    __metaclass__ = abc.ABCMeta

    # Parses a row and returns a tuple with with two elements:
    # 1: datetime.datetime.
    # 2: dictionary or dict-like object.
    @abc.abstractmethod
    def parseRow(self, csvRowDict):
        raise NotImplementedError()

    # Returns a list of field names. If None, then the first row in the CSV should have the field names.
    @abc.abstractmethod
    def getFieldNames(self):
        raise NotImplementedError()

    # Returns the delimiter.
    @abc.abstractmethod
    def getDelimiter(self):
        raise NotImplementedError()


# Interface for bar filters.
class RowFilter(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def includeRow(self, dateTime, values):
        raise NotImplementedError()


class DateRangeFilter(RowFilter):
    def __init__(self, fromDate=None, toDate=None):
        self.__fromDate = fromDate
        self.__toDate = toDate

    def includeRow(self, dateTime, values):
        if self.__toDate and dateTime > self.__toDate:
            return False
        if self.__fromDate and dateTime < self.__fromDate:
            return False
        return True


class BaseFeed(memfeed.MemFeed):
    def __init__(self, rowParser, maxLen=dataseries.DEFAULT_MAX_LEN):
        memfeed.MemFeed.__init__(self, maxLen)
        self.__rowParser = rowParser
        self.__rowFilter = None

    def setRowFilter(self, rowFilter):
        self.__rowFilter = rowFilter

    def addValuesFromCSV(self, path):
        # Load the values from the csv file
        values = []
        reader = csvutils.FastDictReader(open(path, "r"), fieldnames=self.__rowParser.getFieldNames(), delimiter=self.__rowParser.getDelimiter())
        for row in reader:
            dateTime, rowValues = self.__rowParser.parseRow(row)
            if dateTime is not None and (self.__rowFilter is None or self.__rowFilter.includeRow(dateTime, rowValues)):
                values.append((dateTime, rowValues))

        self.addValues(values)


# This row parser doesn't support CSV files that have date and time in different columns.
class BasicRowParser(RowParser):
    def __init__(self, dateTimeColumn, dateTimeFormat, converter, delimiter=",", timezone=None):
        self.__dateTimeColumn = dateTimeColumn
        self.__dateTimeFormat = dateTimeFormat
        self.__converter = converter
        self.__delimiter = delimiter
        self.__timezone = timezone
        self.__timeDelta = None

    def parseRow(self, csvRowDict):
        dateTime = datetime.datetime.strptime(csvRowDict[self.__dateTimeColumn], self.__dateTimeFormat)
        # Localize the datetime if a timezone was given.
        if self.__timezone is not None:
            if self.__timeDelta is not None:
                dateTime += self.__timeDelta
            dateTime = dt.localize(dateTime, self.__timezone)
        # Convert the values
        values = {}
        for key, value in csvRowDict.items():
            if key != self.__dateTimeColumn:
                values[key] = self.__converter(key, value)
        return (dateTime, values)

    def getFieldNames(self):
        return None

    def getDelimiter(self):
        return self.__delimiter

    def setTimeDelta(self, timeDelta):
        self.__timeDelta = timeDelta


def float_or_string(column, value):
    try:
        ret = float(value)
    except Exception:
        ret = value
    return ret


class Feed(BaseFeed):
    """A feed that loads values from CSV formatted files.

    :param dateTimeColumn: The name of the column that has the datetime information.
    :type dateTimeColumn: string.
    :param dateTimeFormat: The datetime format. datetime.datetime.strptime will be used to parse the column.
    :type dateTimeFormat: string.
    :param converter: A function with two parameters (column name and value) used to convert the string
        value to something else. The default coverter will try to convert the value to a float. If that fails
        the original string is returned.
    :type converter: function.
    :param delimiter: The string used to separate values.
    :type delimiter: string.
    :param timezone: The timezone to use to localize datetimes. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param maxLen: The maximum number of values that each :class:`pyalgotrade.dataseries.DataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dateTimeColumn, dateTimeFormat, converter=None, delimiter=",", timezone=None, maxLen=dataseries.DEFAULT_MAX_LEN):
        if converter is None:
            converter = float_or_string
        self.__rowParser = BasicRowParser(dateTimeColumn, dateTimeFormat, converter, delimiter, timezone)
        BaseFeed.__init__(self, self.__rowParser, maxLen)

    def addValuesFromCSV(self, path):
        """Loads values from a file.

        :param path: The path to the CSV file.
        :type path: string.
        """
        return BaseFeed.addValuesFromCSV(self, path)

    def setDateRange(self, fromDateTime, toDateTime):
        self.setRowFilter(DateRangeFilter(fromDateTime, toDateTime))

    def setTimeDelta(self, timeDelta):
        self.__rowParser.setTimeDelta(timeDelta)
