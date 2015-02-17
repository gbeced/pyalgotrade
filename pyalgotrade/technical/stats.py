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

from pyalgotrade import technical
from pyalgotrade import dataseries


class StdDevEventWindow(technical.EventWindow):
    def __init__(self, period, ddof):
        assert(period > 0)
        technical.EventWindow.__init__(self, period)
        self.__ddof = ddof

    def getValue(self):
        ret = None
        if self.windowFull():
            ret = self.getValues().std(ddof=self.__ddof)
        return ret


class StdDev(technical.EventBasedFilter):
    """Standard deviation filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The number of values to use to calculate the Standard deviation.
    :type period: int.
    :param ddof: Delta degrees of freedom.
    :type ddof: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, period, ddof=0, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, StdDevEventWindow(period, ddof), maxLen)


class ZScoreEventWindow(technical.EventWindow):
    def __init__(self, period, ddof):
        assert(period > 1)
        technical.EventWindow.__init__(self, period)
        self.__ddof = ddof

    def getValue(self):
        ret = None
        if self.windowFull():
            values = self.getValues()
            lastValue = values[-1]
            mean = values.mean()
            std = values.std(ddof=self.__ddof)
            ret = (lastValue - mean) / float(std)
        return ret


class ZScore(technical.EventBasedFilter):
    """Z-Score filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The number of values to use to calculate the Z-Score.
    :type period: int.
    :param ddof: Delta degrees of freedom to use for the standard deviation.
    :type ddof: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, period, ddof=0, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, ZScoreEventWindow(period, ddof), maxLen)
