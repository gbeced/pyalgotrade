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
from pyalgotrade.utils import collections
from pyalgotrade.utils import dt

import numpy as np
from scipy import stats


# Using scipy.stats.linregress instead of numpy.linalg.lstsq because of this:
# http://stackoverflow.com/questions/20736255/numpy-linalg-lstsq-with-big-values
def lsreg(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    res = stats.linregress(x, y)
    return res[0], res[1]


class LeastSquaresRegressionWindow(technical.EventWindow):
    def __init__(self, windowSize):
        assert(windowSize > 1)
        technical.EventWindow.__init__(self, windowSize)
        self.__timestamps = collections.NumPyDeque(windowSize)

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        if value is not None:
            timestamp = dt.datetime_to_timestamp(dateTime)
            if len(self.__timestamps):
                assert(timestamp > self.__timestamps[-1])
            self.__timestamps.append(timestamp)

    def __getValueAtImpl(self, timestamp):
        ret = None
        if self.windowFull():
            a, b = lsreg(self.__timestamps.data(), self.getValues())
            ret = a * timestamp + b
        return ret

    def getTimeStamps(self):
        return self.__timestamps

    def getValueAt(self, dateTime):
        return self.__getValueAtImpl(dt.datetime_to_timestamp(dateTime))

    def getValue(self):
        ret = None
        if self.windowFull():
            ret = self.__getValueAtImpl(self.__timestamps.data()[-1])
        return ret


class LeastSquaresRegression(technical.EventBasedFilter):
    """Calculates values based on a least-squares regression.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param windowSize: The number of values to use to calculate the regression.
    :type windowSize: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, windowSize, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, LeastSquaresRegressionWindow(windowSize), maxLen)

    def getValueAt(self, dateTime):
        """Calculates the value at a given time based on the regression line.

        :param dateTime: The datetime to calculate the value at.
            Will return None if there are not enough values in the underlying DataSeries.
        :type dateTime: :class:`datetime.datetime`.
        """
        return self.getEventWindow().getValueAt(dateTime)


class SlopeEventWindow(technical.EventWindow):
    def __init__(self, windowSize):
        technical.EventWindow.__init__(self, windowSize)
        self.__x = np.asarray(range(windowSize))

    def getValue(self):
        ret = None
        if self.windowFull():
            y = self.getValues()
            ret = lsreg(self.__x, y)[0]
        return ret


class Slope(technical.EventBasedFilter):
    """The Slope filter calculates the slope of a least-squares regression line.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The number of values to use to calculate the slope.
    :type period: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.

    .. note::
        This filter ignores the time ellapsed between the different values.
    """

    def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, SlopeEventWindow(period), maxLen)

    def getTrendDays(self):
        return self.getWindowSize()


class TrendEventWindow(SlopeEventWindow):
    def __init__(self, windowSize, positiveThreshold, negativeThreshold):
        if negativeThreshold > positiveThreshold:
            raise Exception("Invalid thresholds")

        SlopeEventWindow.__init__(self, windowSize)
        self.__positiveThreshold = positiveThreshold
        self.__negativeThreshold = negativeThreshold

    def getValue(self):
        ret = SlopeEventWindow.getValue(self)
        if ret is not None:
            if ret > self.__positiveThreshold:
                ret = True
            elif ret < self.__negativeThreshold:
                ret = False
            else:  # Between negative and postive thresholds.
                ret = None
        return ret


class Trend(technical.EventBasedFilter):
    def __init__(self, dataSeries, trendDays, positiveThreshold=0, negativeThreshold=0, maxLen=dataseries.DEFAULT_MAX_LEN):
        technical.EventBasedFilter.__init__(self, dataSeries, TrendEventWindow(trendDays, positiveThreshold, negativeThreshold), maxLen)
