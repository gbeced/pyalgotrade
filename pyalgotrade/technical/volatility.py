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
import numpy as np 


# This event window will calculate and hold percent-change values.
class VOLATILITYEventWindow(technical.EventWindow):
    def __init__(self, period, multiple, useAdjustedValues):
        assert(period > 1)
        super(VOLATILITYEventWindow, self).__init__(period)
        self.__multiple = multiple 
        self.__useAdjustedValues = useAdjustedValues
        self.__prevClose = None
        self.__value = None

    def _calculatePctChange(self, value):
        ret = None
        if self.__prevClose is None:
            ret = None
        else:
            try: 
                ret = 100*(value.getClose(self.__useAdjustedValues) - self.__prevClose) / value.getClose(self.__useAdjustedValues)
            except: 
                ret = None 
        return ret

    def onNewValue(self, dateTime, value):
        pc = self._calculatePctChange(value)
        if pc != None: 
            super(VOLATILITYEventWindow, self).onNewValue(dateTime, pc)
        self.__prevClose = value.getClose(self.__useAdjustedValues)
        if value is not None and self.windowFull():
            self.__value = self.getValues().std() 

    def getValue(self):
        if self.__value != None: 
            return self.__value * self.__multiple
        else: 
            return self.__value 


class VOLATILITY(technical.EventBasedFilter):
    """Volatility Filter 

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param period: The average period. Must be > 1.
    :type period: int.
    :param multiple: The number by which the Volatility value is multiplied. Must be > 0 
    :type multiple: float  
    :param useAdjustedValues: True to use adjusted Low/High/Close values.
    :type useAdjustedValues: boolean.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, barDataSeries, period=252, multiple=1, useAdjustedValues=True, maxLen=None):
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")

        super(VOLATILITY, self).__init__(barDataSeries, VOLATILITYEventWindow(period, multiple, useAdjustedValues), maxLen)
