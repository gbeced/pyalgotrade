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
.. moduleauthor:: xmph <xmph.forex@gmail.com>
"""

from pyalgotrade import dataseries
from pyalgotrade.technical import highlow

class DonchianBands(object):
    """Donchian Bands
        UPPER band is represented as highest from high of last n closing bars
        LOWER band is represented as lowest from low of last n closing bars

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: The number of values to use in the calculation. Must be > 1.
    :type period: int.
    :param lag: lag to be applied to signal (0=no lag) in terms of barFeed period
    :type lag: int.
    """

    def __init__(self, dataSeries, period, lag=0, maxLen=dataseries.DEFAULT_MAX_LEN):
        self.__high = highlow.High(dataSeries, period, maxLen=maxLen)
        self.__low = highlow.Low(dataSeries, period, maxLen=maxLen)
        self.__upperBand = dataseries.SequenceDataSeries(maxLen)
        self.__lowerBand = dataseries.SequenceDataSeries(maxLen)
        
        self.__lag = -(2+lag) # starts at 2 considering [-1] is current bar
        # It is important to subscribe after highlow since we'll use those values.
        dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def __onNewValue(self, dataSeries, dateTime, value):
        upperValue = None
        lowerValue = None

        if value is not None:
            high = self.__high[-1]
            if high is not None and len(self.__high) > -self.__lag:
                upperValue = self.__high[self.__lag]
                lowerValue = self.__low[self.__lag]

        self.__upperBand.appendWithDateTime(dateTime, upperValue)
        self.__lowerBand.appendWithDateTime(dateTime, lowerValue)

    def getUpperBand(self):
        """
        Returns the upper band as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__upperBand

    def getLowerBand(self):
        """
        Returns the lower band as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__lowerBand