# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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


def lsreg(x, y):
    x = np.array(x)
    y = np.array(y)
    A = np.vstack([x, np.ones(len(x))]).T
    return np.linalg.lstsq(A, y)[0]


class LeastSquaresRegressionWindow(technical.EventWindow):
    def __init__(self, windowSize):
        assert(windowSize > 1)
        technical.EventWindow.__init__(self, windowSize)
        self.__timestamps = collections.ListDeque(windowSize)

    def onNewValue(self, dateTime, value):
        technical.EventWindow.onNewValue(self, dateTime, value)
        if value is not None:
            self.__timestamps.append(dt.datetime_to_timestamp(dateTime))

    def __getValueAtImpl(self, timestamp):
        ret = None
        if self.windowFull():
            a, b = lsreg(self.__timestamps.data(), self.getValues())
            ret = a * timestamp + b
        return ret

    def getValueAt(self, dateTime):
        return self.__getValueAtImpl(dt.datetime_to_timestamp(dateTime))

    def getValue(self):
        ret = None
        if self.windowFull():
            ret = self.__getValueAtImpl(self.__timestamps.data()[-1])
        return ret

class LeastSquaresRegression(technical.EventBasedFilter):
    """Calculates values based on least-squares regression.

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
