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

import numpy as np

from pyalgotrade import technical
from pyalgotrade import dataseries


# Code Tom Starke for the Hurst Exponent.
def hurst_exp(p, lags):
    tau = []
    lagvec = []

    #  Step through the different lags
    for lag in range(2, lags):
        #  produce price difference with lag
        pp = np.subtract(p[lag:], p[:-lag])
        #  Write the different lags into a vector
        lagvec.append(lag)
        #  Calculate the variance of the differnce vector
        tau.append(np.sqrt(np.std(pp)))
    # linear fit to double-log graph (gives power)
    m = np.polyfit(np.log10(lagvec), np.log10(tau), 1)
    # calculate hurst
    hurst = m[0]*2
    return hurst


class HurstExponentEventWindow(technical.EventWindow):
    def __init__(self, period, lags, logValues=True):
        technical.EventWindow.__init__(self, period)
        self.__lags = lags
        self.__logValues = logValues

    def onNewValue(self, dateTime, value):
        if value is not None and self.__logValues:
            value = np.log10(value)
        technical.EventWindow.onNewValue(self, dateTime, value)

    def getValue(self):
        ret = None
        if self.windowFull():
            ret = hurst_exp(self.getValues(), self.__lags)
        return ret


class HurstExponent(technical.EventBasedFilter):
    """Hurst exponent filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The number of values to use to calculate the hurst exponent.
    :type period: int.
    :param lags: The number of lags to use. Must be > 2.
    :type lags: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, dataSeries, period, lags, logValues=True, maxLen=dataseries.DEFAULT_MAX_LEN):
        assert period > 0, "period must be > 0"
        assert lags > 2, "lags must be > 2"
        technical.EventBasedFilter.__init__(
            self,
            dataSeries,
            HurstExponentEventWindow(period, lags, logValues),
            maxLen
        )
