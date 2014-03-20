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

from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.technical import ma


class BarWrapper(object):
    def __init__(self, useAdjusted):
        self.__useAdjusted = useAdjusted

    def getLow(self, bar_):
        return bar_.getLow(self.__useAdjusted)

    def getHigh(self, bar_):
        return bar_.getHigh(self.__useAdjusted)

    def getClose(self, bar_):
        return bar_.getClose(self.__useAdjusted)


def get_low_high_values(barWrapper, bars):
    currBar = bars[0]
    lowestLow = barWrapper.getLow(currBar)
    highestHigh = barWrapper.getHigh(currBar)
    for i in range(len(bars)):
        currBar = bars[i]
        lowestLow = min(lowestLow, barWrapper.getLow(currBar))
        highestHigh = max(highestHigh, barWrapper.getHigh(currBar))
    return (lowestLow, highestHigh)


class SOEventWindow(technical.EventWindow):
    def __init__(self, period, useAdjustedValues):
        assert(period > 1)
        technical.EventWindow.__init__(self, period, dtype=object)
        self.__barWrapper = BarWrapper(useAdjustedValues)

    def getValue(self):
        ret = None
        if self.windowFull():
            lowestLow, highestHigh = get_low_high_values(self.__barWrapper, self.getValues())
            currentClose = self.__barWrapper.getClose(self.getValues()[-1])
            ret = (currentClose - lowestLow) / float(highestHigh - lowestLow) * 100
        return ret


class StochasticOscillator(technical.EventBasedFilter):
    """Stochastic Oscillator filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:stochastic_oscillato.
    Note that the value returned by this filter is %K. To access %D use :meth:`getD`.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param period: The period. Must be > 1.
    :type period: int.
    :param dSMAPeriod: The %D SMA period. Must be > 1.
    :type dSMAPeriod: int.
    :param useAdjustedValues: True to use adjusted Low/High/Close values.
    :type useAdjustedValues: boolean.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, barDataSeries, period, dSMAPeriod=3, useAdjustedValues=False, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert(dSMAPeriod > 1)
        technical.EventBasedFilter.__init__(self, barDataSeries, SOEventWindow(period, useAdjustedValues), maxLen)
        self.__d = ma.SMA(self, dSMAPeriod, maxLen)

    def getD(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the %D values."""
        return self.__d
