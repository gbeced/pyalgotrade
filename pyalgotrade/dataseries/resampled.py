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

from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from pyalgotrade import bar
from pyalgotrade import resamplebase


class AggFunGrouper(resamplebase.Grouper):
    def __init__(self, groupDateTime, value, aggfun):
        super(AggFunGrouper, self).__init__(groupDateTime)
        self.__values = [value]
        self.__aggfun = aggfun

    def addValue(self, value):
        self.__values.append(value)

    def getGrouped(self):
        return self.__aggfun(self.__values)


class BarGrouper(resamplebase.Grouper):
    def __init__(self, groupDateTime, bar_, frequency):
        super(BarGrouper, self).__init__(groupDateTime)
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
            self.__open, self.__high, self.__low, self.__close, self.__volume, self.__adjClose,
            self.__frequency
        )
        ret.setUseAdjustedValue(self.__useAdjValue)
        return ret


class DSResampler(object, metaclass=abc.ABCMeta):
    def initDSResampler(self, dataSeries, frequency):
        if not resamplebase.is_valid_frequency(frequency):
            raise Exception("Unsupported frequency")

        self.__frequency = frequency
        self.__grouper = None
        self.__range = None

        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    @abc.abstractmethod
    def buildGrouper(self, range_, value, frequency):
        raise NotImplementedError()

    def __onNewValue(self, dataSeries, dateTime, value):
        if self.__range is None:
            self.__range = resamplebase.build_range(dateTime, self.__frequency)
            self.__grouper = self.buildGrouper(self.__range, value, self.__frequency)
        elif self.__range.belongs(dateTime):
            self.__grouper.addValue(value)
        else:
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__range = resamplebase.build_range(dateTime, self.__frequency)
            self.__grouper = self.buildGrouper(self.__range, value, self.__frequency)

    def pushLast(self):
        if self.__grouper is not None:
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__grouper = None
            self.__range = None

    def checkNow(self, dateTime):
        if self.__range is not None and not self.__range.belongs(dateTime):
            self.appendWithDateTime(self.__grouper.getDateTime(), self.__grouper.getGrouped())
            self.__grouper = None
            self.__range = None


class ResampledBarDataSeries(bards.BarDataSeries, DSResampler):
    """A BarDataSeries that will build on top of another, higher frequency, BarDataSeries.
    Resampling will take place as new values get pushed into the dataseries being resampled.

    :param dataSeries: The DataSeries instance being resampled.
    :type dataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`
    :param frequency: The grouping frequency in seconds. Must be > 0.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.

    .. note::
        * Supported resampling frequencies are:
            * Less than bar.Frequency.DAY
            * bar.Frequency.DAY
            * bar.Frequency.MONTH
    """

    def __init__(self, dataSeries, frequency, maxLen=None):
        if not isinstance(dataSeries, bards.BarDataSeries):
            raise Exception("dataSeries must be a dataseries.bards.BarDataSeries instance")

        super(ResampledBarDataSeries, self).__init__(maxLen)
        self.initDSResampler(dataSeries, frequency)

    def checkNow(self, dateTime):
        """Forces a resample check. Depending on the resample frequency, and the current datetime, a new
        value may be generated.

       :param dateTime: The current datetime.
       :type dateTime: :class:`datetime.datetime`
        """

        return super(ResampledBarDataSeries, self).checkNow(dateTime)

    def buildGrouper(self, range_, value, frequency):
        return BarGrouper(range_.getBeginning(), value, frequency)


class ResampledDataSeries(dataseries.SequenceDataSeries, DSResampler):
    def __init__(self, dataSeries, frequency, aggfun, maxLen=None):
        super(ResampledDataSeries, self).__init__(maxLen)
        self.initDSResampler(dataSeries, frequency)
        self.__aggfun = aggfun

    def buildGrouper(self, range_, value, frequency):
        return AggFunGrouper(range_.getBeginning(), value, self.__aggfun)
