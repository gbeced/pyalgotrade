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

from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards


class Line(object):
    """A line in a line break chart."""

    def __init__(self, low, high, dateTime, white):
        self.__low = low
        self.__high = high
        self.__dateTime = dateTime
        self.__white = white

    def getDateTime(self):
        """The datetime."""
        return self.__dateTime

    def getLow(self):
        """The low value."""
        return self.__low

    def getHigh(self):
        """The high value."""
        return self.__high

    def isWhite(self):
        """True if the line is white (rising prices)."""
        return self.__white

    def isBlack(self):
        """True if the line is black (falling prices)."""
        return not self.__white


class LineBreak(dataseries.SequenceDataSeries):
    """Line Break filter as described in http://stockcharts.com/school/doku.php?id=chart_school:chart_analysis:three_line_break.
    .
    This is a DataSeries of :class:`Line` instances.

    :param barDataSeries: The DataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param reversalLines: The number of lines back to check to calculate a reversal. Must be greater than 1.
    :type reversalLines: int.
    :param useAdjustedValues: True to use adjusted high/low/close values.
    :type useAdjustedValues: boolean.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
        This value can't be smaller than reversalLines.
    :type maxLen: int.
    """

    def __init__(self, barDataSeries, reversalLines, useAdjustedValues=False, maxLen=None):
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")
        if reversalLines < 2:
            raise Exception("reversalLines must be greater than 1")
        if dataseries.get_checked_max_len(maxLen) < reversalLines:
            raise Exception("maxLen can't be smaller than reversalLines")

        super(LineBreak, self).__init__(maxLen)

        self.__reversalLines = reversalLines
        self.__useAdjustedValues = useAdjustedValues

        barDataSeries.getNewValueEvent().subscribe(self.__onNewBar)

    def __onNewBar(self, dataSeries, dateTime, value):
        line = self.__getNextLine(value)
        if line is not None:
            self.appendWithDateTime(dateTime, line)

    def __isReversal(self, value, breakUp):
        assert(len(self))
        lines = self[self.__reversalLines*-1:]
        if breakUp:
            breakPoint = max([line.getHigh() for line in lines])
            ret = value > breakPoint
        else:
            breakPoint = min([line.getLow() for line in lines])
            ret = value < breakPoint
        return ret

    def __getNextLine(self, bar):
        ret = None

        if len(self) > 0:
            lastLine = self[-1]
            close = bar.getClose(self.__useAdjustedValues)
            if lastLine.isWhite():
                if close > lastLine.getHigh():
                    # Price extends in the same direction
                    ret = Line(lastLine.getHigh(), close, bar.getDateTime(), True)
                elif self.__isReversal(close, False):
                    # Price change is enough to warrant a reversal.
                    ret = Line(close, lastLine.getLow(), bar.getDateTime(), False)
            else:
                if close < lastLine.getLow():
                    # Price extends in the same direction
                    ret = Line(close, lastLine.getLow(), bar.getDateTime(), False)
                elif self.__isReversal(close, True):
                    # Price change is enough to warrant a reversal.
                    ret = Line(lastLine.getHigh(), close, bar.getDateTime(), True)
        else:
            white = False
            if bar.getClose(self.__useAdjustedValues) >= bar.getOpen(self.__useAdjustedValues):
                white = True
            ret = Line(bar.getLow(self.__useAdjustedValues), bar.getHigh(self.__useAdjustedValues), bar.getDateTime(), white)
        return ret

    def setMaxLen(self, maxLen):
        if maxLen < self.__reversalLines:
            raise Exception("maxLen can't be smaller than reversalLines")
        super(LineBreak, self).setMaxLen(maxLen)
