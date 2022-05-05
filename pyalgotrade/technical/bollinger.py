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

from pyalgotrade import dataseries
from pyalgotrade.technical import ma
from pyalgotrade.technical import stats
from pyalgotrade.dataseries import bards


class BollingerBands(object):
    """Bollinger Bands filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:bollinger_bands.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param period: The number of values to use in the calculation. Must be > 1.
    :type period: int.
    :param numStdDev: The number of standard deviations to use for the upper and lower bands.
    :type numStdDev: int.
    :param band: "upper", "middle", or "lower" band  OR "bandwidth"
    :type band: str
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, barDataSeries, period, numStdDev, price_type="Typical", band="bandwidth", maxLen=None):
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")
        if price_type == "High":
            dataSeries = barDataSeries.getHighDataSeries()
        elif price_type == "Low": 
            dataSeries = barDataSeries.getLowDataSeries()
        elif price_type == "Close": 
            dataSeries = barDataSeries.getAdjCloseDataSeries()
        elif price_type == "Typical":
            dataSeries = barDataSeries.getTypicalPriceDataSeries()
        else: 
            raise ValueError(f"'price_type' must be either 'High', 'Low', 'Close', or 'Typical'")

        self.__sma = ma.SMA(dataSeries, period, maxLen=maxLen)
        self.__stdDev = stats.StdDev(dataSeries, period, maxLen=maxLen)
        self.__upperBand = dataseries.SequenceDataSeries(maxLen)
        self.__lowerBand = dataseries.SequenceDataSeries(maxLen)
        self.__numStdDev = numStdDev
        self.band = band 
        # It is important to subscribe after sma and stddev since we'll use those values.
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def __onNewValue(self, dataSeries, dateTime, value):
        upperValue = None
        lowerValue = None

        if value is not None:
            sma = self.__sma[-1]
            if sma is not None:
                stdDev = self.__stdDev[-1]
                upperValue = sma + stdDev * self.__numStdDev
                lowerValue = sma + stdDev * self.__numStdDev * -1

        self.__upperBand.appendWithDateTime(dateTime, upperValue)
        self.__lowerBand.appendWithDateTime(dateTime, lowerValue)

    def getUpperBand(self):
        """
        Returns the upper band as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__upperBand

    def getMiddleBand(self):
        """
        Returns the middle band as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__sma

    def getLowerBand(self):
        """
        Returns the lower band as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__lowerBand

    def getValue(self): 
        '''
        Return last value of chosen band 
        
        ''' 
        if self.band == "upper": 
            return self.getUpperBand()[-1]
        elif self.band == "middle":
            return self.getMiddleBand()[-1]
        elif self.band == "lower":
            return self.getLowerBand()[-1]
        elif self.band == "bandwidth": 
            return (self.getUpperBand()[-1] - self.getLowerBand()[-1]) / self.getMiddleBand()[-1]
        else: 
            raise ValueError(f"Band type {self.band} is not available. Choices are 'upper', \
                  'middle', or 'lower'")