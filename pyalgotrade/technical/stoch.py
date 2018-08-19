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

from pyalgotrade import technical
from pyalgotrade.dataseries import bards
from pyalgotrade.technical import ma


def get_low_high_values(useAdjusted, bars):
    currBar = bars[0]
    lowestLow = currBar.getLow(useAdjusted)
    highestHigh = currBar.getHigh(useAdjusted)
    for i in range(len(bars)):
        currBar = bars[i]
        lowestLow = min(lowestLow, currBar.getLow(useAdjusted))
        highestHigh = max(highestHigh, currBar.getHigh(useAdjusted))
    return (lowestLow, highestHigh)


class SOEventWindow(technical.EventWindow):
    def __init__(self, period, useAdjustedValues):
        assert(period > 1)
        super(SOEventWindow, self).__init__(period, dtype=object)
        self.__useAdjusted = useAdjustedValues

    def getValue(self):
        ret = None
        if self.windowFull():
            lowestLow, highestHigh = get_low_high_values(self.__useAdjusted, self.getValues())
            currentClose = self.getValues()[-1].getClose(self.__useAdjusted)
            closeDelta = currentClose - lowestLow
            if closeDelta:
                ret = closeDelta / float(highestHigh - lowestLow) * 100
            else:
                ret = 0.0
        return ret


class StochasticOscillator(technical.EventBasedFilter):
    """Fast Stochastic Oscillator filter as described in
    http://stockcharts.com/school/doku.php?st=stochastic+oscillator&id=chart_school:technical_indicators:stochastic_oscillator_fast_slow_and_full.
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
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, barDataSeries, period, dSMAPeriod=3, useAdjustedValues=False, maxLen=None):
        assert dSMAPeriod > 1, "dSMAPeriod must be > 1"
        assert isinstance(barDataSeries, bards.BarDataSeries), \
            "barDataSeries must be a dataseries.bards.BarDataSeries instance"

        super(StochasticOscillator, self).__init__(barDataSeries, SOEventWindow(period, useAdjustedValues), maxLen)
        self.__d = ma.SMA(self, dSMAPeriod, maxLen)

    def getD(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the %D values."""
        return self.__d
