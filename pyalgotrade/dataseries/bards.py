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

import six


class BarDataSeries(dataseries.SequenceDataSeries):
    """A DataSeries of :class:`pyalgotrade.bar.Bar` instances.

    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, useAdjustedValues=True, maxLen=None):
        super(BarDataSeries, self).__init__(maxLen)
        self.__openDS = dataseries.SequenceDataSeries(maxLen)
        self.__closeDS = dataseries.SequenceDataSeries(maxLen)
        self.__highDS = dataseries.SequenceDataSeries(maxLen)
        self.__lowDS = dataseries.SequenceDataSeries(maxLen)
        self.__typicalDS = dataseries.SequenceDataSeries(maxLen)
        self.__volumeDS = dataseries.SequenceDataSeries(maxLen)
        
        self.__adjOpenDS = dataseries.SequenceDataSeries(maxLen)
        self.__adjCloseDS = dataseries.SequenceDataSeries(maxLen)
        self.__adjHighDS = dataseries.SequenceDataSeries(maxLen)
        self.__adjLowDS = dataseries.SequenceDataSeries(maxLen)
        self.__adjTypicalDS = dataseries.SequenceDataSeries(maxLen)
        
        self.__extraDS = {}
        self.__useAdjustedValues = useAdjustedValues 

    def __getOrCreateExtraDS(self, name):
        ret = self.__extraDS.get(name)
        if ret is None:
            ret = dataseries.SequenceDataSeries(self.getMaxLen())
            self.__extraDS[name] = ret
        return ret

    def setUseAdjustedValues(self, useAdjusted):
        self.__useAdjustedValues = useAdjusted

    def append(self, bar):
        self.appendWithDateTime(bar.getDateTime(), bar)

    def appendWithDateTime(self, dateTime, bar):
        assert(dateTime is not None)
        assert(bar is not None)
        
        bar.setUseAdjustedValue(self.__useAdjustedValues)
        super(BarDataSeries, self).appendWithDateTime(dateTime, bar)

        self.__openDS.appendWithDateTime(dateTime, bar.getOpen())
        self.__closeDS.appendWithDateTime(dateTime, bar.getClose())
        self.__highDS.appendWithDateTime(dateTime, bar.getHigh())
        self.__lowDS.appendWithDateTime(dateTime, bar.getLow())
        self.__typicalDS.appendWithDateTime(dateTime, (bar.getOpen()+bar.getLow()+bar.getClose())/3)
        
        self.__volumeDS.appendWithDateTime(dateTime, bar.getVolume())
        
        self.__adjOpenDS.appendWithDateTime(dateTime, bar.getOpen(self.__useAdjustedValues))
        self.__adjCloseDS.appendWithDateTime(dateTime, bar.getAdjClose())
        self.__adjHighDS.appendWithDateTime(dateTime, bar.getHigh(self.__useAdjustedValues))
        self.__adjLowDS.appendWithDateTime(dateTime, bar.getLow(self.__useAdjustedValues))
        self.__adjTypicalDS.appendWithDateTime(dateTime, \
            (bar.getOpen(self.__useAdjustedValues)+bar.getLow(self.__useAdjustedValues)+bar.getClose(self.__useAdjustedValues))/3)
        
        # Process extra columns.
        for name, value in six.iteritems(bar.getExtraColumns()):
            extraDS = self.__getOrCreateExtraDS(name)
            extraDS.appendWithDateTime(dateTime, value)

    def getOpenDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the open prices."""
        return self.__openDS

    def getCloseDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the close prices."""
        return self.__closeDS

    def getHighDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the high prices."""
        return self.__highDS

    def getLowDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the low prices."""
        return self.__lowDS

    def getTypicalDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the typical prices."""
        return self.__typicalDS
        
    def getVolumeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the volume."""
        return self.__volumeDS

    def getAdjOpenDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted open prices."""
        return self.__adjOpenDS

    def getAdjCloseDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted close prices."""
        return self.__adjCloseDS

    def getAdjHighDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted high prices."""
        return self.__AdjHighDS

    def getAdjLowDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted low prices."""
        return self.__adjLowDS

    def getAdjTypicalDataSeries(self):
            """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted typical prices."""
            return self.__adjTypicalDS

    def getPriceDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the close or adjusted close prices."""
        if self.__useAdjustedValues:
            return self.__adjCloseDS
        else:
            return self.__closeDS

    def getExtraDataSeries(self, name):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` for an extra column."""
        return self.__getOrCreateExtraDS(name)
