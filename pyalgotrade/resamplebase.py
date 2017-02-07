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


import abc
import datetime

from pyalgotrade.utils import dt
from pyalgotrade import bar


class TimeRange(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def belongs(self, dateTime):
        raise NotImplementedError()

    @abc.abstractmethod
    def getBeginning(self):
        raise NotImplementedError()

    # 1 past the end
    @abc.abstractmethod
    def getEnding(self):
        raise NotImplementedError()


class IntraDayRange(TimeRange):
    def __init__(self, dateTime, frequency):
        super(IntraDayRange, self).__init__()
        assert isinstance(frequency, int)
        assert frequency > 1
        assert frequency < bar.Frequency.DAY

        ts = int(dt.datetime_to_timestamp(dateTime))
        slot = int(ts / frequency)
        slotTs = slot * frequency
        self.__begin = dt.timestamp_to_datetime(slotTs, not dt.datetime_is_naive(dateTime))
        if not dt.datetime_is_naive(dateTime):
            self.__begin = dt.localize(self.__begin, dateTime.tzinfo)
        self.__end = self.__begin + datetime.timedelta(seconds=frequency)

    def belongs(self, dateTime):
        return dateTime >= self.__begin and dateTime < self.__end

    def getBeginning(self):
        return self.__begin

    def getEnding(self):
        return self.__end


class DayRange(TimeRange):
    def __init__(self, dateTime):
        super(DayRange, self).__init__()
        self.__begin = datetime.datetime(dateTime.year, dateTime.month, dateTime.day)
        if not dt.datetime_is_naive(dateTime):
            self.__begin = dt.localize(self.__begin, dateTime.tzinfo)
        self.__end = self.__begin + datetime.timedelta(days=1)

    def belongs(self, dateTime):
        return dateTime >= self.__begin and dateTime < self.__end

    def getBeginning(self):
        return self.__begin

    def getEnding(self):
        return self.__end


class MonthRange(TimeRange):
    def __init__(self, dateTime):
        super(MonthRange, self).__init__()
        self.__begin = datetime.datetime(dateTime.year, dateTime.month, 1)

        # Calculate the ending date.
        if dateTime.month == 12:
            self.__end = datetime.datetime(dateTime.year + 1, 1, 1)
        else:
            self.__end = datetime.datetime(dateTime.year, dateTime.month + 1, 1)

        if not dt.datetime_is_naive(dateTime):
            self.__begin = dt.localize(self.__begin, dateTime.tzinfo)
            self.__end = dt.localize(self.__end, dateTime.tzinfo)

    def belongs(self, dateTime):
        return dateTime >= self.__begin and dateTime < self.__end

    def getBeginning(self):
        return self.__begin

    def getEnding(self):
        return self.__end


def is_valid_frequency(frequency):
    assert(isinstance(frequency, int))
    assert(frequency > 1)

    if frequency < bar.Frequency.DAY:
        ret = True
    elif frequency == bar.Frequency.DAY:
        ret = True
    elif frequency == bar.Frequency.MONTH:
        ret = True
    else:
        ret = False
    return ret


def build_range(dateTime, frequency):
    assert(isinstance(frequency, int))
    assert(frequency > 1)

    if frequency < bar.Frequency.DAY:
        ret = IntraDayRange(dateTime, frequency)
    elif frequency == bar.Frequency.DAY:
        ret = DayRange(dateTime)
    elif frequency == bar.Frequency.MONTH:
        ret = MonthRange(dateTime)
    else:
        raise Exception("Unsupported frequency")
    return ret


class Grouper(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, groupDateTime):
        self.__groupDateTime = groupDateTime

    def getDateTime(self):
        return self.__groupDateTime

    @abc.abstractmethod
    def addValue(self, value):
        """Add a value to the group."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getGrouped(self):
        """Return the grouped value."""
        raise NotImplementedError()
