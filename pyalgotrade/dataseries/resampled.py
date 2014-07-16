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

import abc

from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from pyalgotrade import bar
from pyalgotrade.utils import dt


# Returns the slot's beginning datetime.
# frequency in seconds
def get_slot_datetime(dateTime, frequency):
    ts = int(dt.datetime_to_timestamp(dateTime))
    slot = ts / frequency
    slotTs = slot * frequency
    ret = dt.timestamp_to_datetime(slotTs, False)
    if not dt.datetime_is_naive(dateTime):
        ret = dt.localize(ret, dateTime.tzinfo)
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


class BarGrouper(Grouper):
    def __init__(self, groupDateTime, bar_, frequency):
        Grouper.__init__(self, groupDateTime)
        self.__open = bar_.getOpen()
        self.__high = bar_.getHigh()
        self.__low = bar_.getLow()
        self.__close = bar_.getClose()
        self.__volume = bar_.getVolume()
        self.__adjClose = bar_.getAdjClose()
        self.__useAdjValue = bar_.getUseAdjValue()
        self.__frequency = frequency

    def addValue(self, value):
        self.__high = max(self.__high, value.getHigh())
        self.__low = min(self.__low, value.getLow())
        self.__close = value.getClose()
        self.__adjClose = value.getAdjClose()
        self.__volume += value.getVolume()

    def getGrouped(self):
        """Return the grouped value."""
        ret = bar.BasicBar(
            self.getDateTime(),
            self.__open,
            self.__high,
            self.__low,
            self.__close,
            self.__volume,
            self.__adjClose,
            self.__frequency
        )
        ret.setUseAdjustedValue(self.__useAdjValue)
        return ret


class ResampledBarDataSeries(bards.BarDataSeries):
    """A BarDataSeries that will build on top of another, higher frequency, BarDataSeries.
    Resampling will take place as new values get pushed into the dataseries being resampled.

    :param dataSeries: The DataSeries instance being resampled.
    :type dataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`
    :param frequency: The grouping frequency in seconds. Must be > 0.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
        bards.BarDataSeries.__init__(self, maxLen)

        if not isinstance(dataSeries, bards.BarDataSeries):
            raise Exception("dataSeries must be a dataseries.bards.BarDataSeries instance")

        if frequency > 0:
            self.__frequency = frequency
        else:
            raise Exception("Invalid frequency")

        self.__grouper = None
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def pushLast(self):
        if self.__grouper is not None:
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__grouper = None

    def __onNewValue(self, dataSeries, dateTime, value):
        slotDateTime = get_slot_datetime(dateTime, self.__frequency)

        if self.__grouper is None:
            self.__grouper = BarGrouper(slotDateTime, value, self.__frequency)
        elif self.__grouper.getDateTime() == slotDateTime:
            self.__grouper.addValue(value)
        else:
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__grouper = BarGrouper(slotDateTime, value, self.__frequency)

    def checkNow(self, dateTime):
        """Forces a resample check. Depending on the resample frequency, and the current datetime, a new
        value may be generated.

       :param dateTime: The current datetime.
       :type dateTime: :class:`datetime.datetime`
        """
        slotDateTime = get_slot_datetime(dateTime, self.__frequency)
        if self.__grouper is not None and self.__grouper.getDateTime() != slotDateTime:
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__grouper = None
