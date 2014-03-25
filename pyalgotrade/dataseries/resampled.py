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


class Slot(object):
    def __init__(self, dateTime, bar_, frequency):
        self.__dateTime = dateTime
        self.__open = bar_.getOpen()
        self.__high = bar_.getHigh()
        self.__low = bar_.getLow()
        self.__close = bar_.getClose()
        self.__volume = bar_.getVolume()
        self.__adjClose = bar_.getAdjClose()
        self.__frequency = frequency

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self):
        return self.__open

    def getHigh(self):
        return self.__high

    def getLow(self):
        return self.__low

    def getClose(self):
        return self.__close

    def getVolume(self):
        return self.__volume

    def getAdjClose(self):
        return self.__adjClose

    def addBar(self, bar_):
        self.__high = max(self.__high, bar_.getHigh())
        self.__low = min(self.__low, bar_.getLow())
        self.__close = bar_.getClose()
        self.__adjClose = bar_.getAdjClose()
        self.__volume += bar_.getVolume()

    def buildBasicBar(self):
        return bar.BasicBar(self.__dateTime, self.__open, self.__high, self.__low, self.__close, self.__volume, self.__adjClose, self.__frequency)


class ResampledBarDataSeries(bards.BarDataSeries):
    """A BarDataSeries that will build on top of another, higher frequency, BarDataSeries.

    :param dataSeries: The DataSeries instance being resampled.
    :type dataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param frequency: The grouping frequency in seconds. Must be > 0.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
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

        self.__slot = None
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def pushLast(self):
        if self.__slot is not None:
            self.appendWithDateTime(self.__slot.getDateTime(), self.__slot.buildBasicBar())
        self.__slot = None

    def __onNewValue(self, dataSeries, dateTime, value):
        dateTime = get_slot_datetime(value.getDateTime(), self.__frequency)

        if self.__slot is None:
            self.__slot = Slot(dateTime, value, self.__frequency)
        elif self.__slot.getDateTime() == dateTime:
            self.__slot.addBar(value)
        else:
            self.appendWithDateTime(self.__slot.getDateTime(), self.__slot.buildBasicBar())
            self.__slot = Slot(dateTime, value, self.__frequency)
