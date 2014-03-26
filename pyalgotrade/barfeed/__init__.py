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

import abc

from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from pyalgotrade import feed


# This is only for backward compatibility since Frequency used to be defined here and not in bar.py.
Frequency = bar.Frequency


class BaseBarFeed(feed.BaseFeed):
    """Base class for :class:`pyalgotrade.bar.Bar` providing feeds.

    :param frequency: The bars frequency. Valid values defined in :class:`pyalgotrade.bar.Frequency`.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
        feed.BaseFeed.__init__(self, maxLen)
        if not maxLen > 0:
            raise Exception("Invalid maximum length")
        self.__defaultInstrument = None
        self.__currentBars = None
        self.__lastBars = {}
        self.__frequency = frequency
        self.__prevDateTime = None

    # Return True if bars provided have adjusted close values.
    @abc.abstractmethod
    def barsHaveAdjClose(self):
        raise NotImplementedError()

    # Subclasses should implement this and return a pyalgotrade.bar.Bars or None if there are no bars.
    @abc.abstractmethod
    def getNextBars(self):
        """Override to return the next :class:`pyalgotrade.bar.Bars` in the feed or None if there are no bars.

        .. note::
            This is for BaseBarFeed subclasses and it should not be called directly.
        """
        raise NotImplementedError()

    def createDataSeries(self, key, maxLen):
        return bards.BarDataSeries(maxLen)

    def getNextValues(self):
        dateTime = None
        bars = self.getNextBars()
        if bars is not None:
            dateTime = bars.getDateTime()

            # Check that current bar datetimes are greater than the previous one.
            if self.__prevDateTime is not None and self.__prevDateTime >= dateTime:
                raise Exception("Bar date times are not in order. Previous datetime was %s and current datetime is %s" % (self.__prevDateTime, dateTime))
            self.__prevDateTime = dateTime

            # Update self.__currentBars and self.__lastBars
            self.__currentBars = bars
            for instrument in bars.getInstruments():
                self.__lastBars[instrument] = bars[instrument]
        return (dateTime, bars)

    def getFrequency(self):
        return self.__frequency

    def getCurrentBars(self):
        """Returns the current :class:`pyalgotrade.bar.Bars`."""
        return self.__currentBars

    def getLastBar(self, instrument):
        """Returns the last :class:`pyalgotrade.bar.Bar` for a given instrument, or None."""
        return self.__lastBars.get(instrument, None)

    def getNewBarsEvent(self):
        # This is for backwards compatibility purposes.
        return self.getNewValuesEvent()

    def getDefaultInstrument(self):
        """Returns the default instrument."""
        return self.__defaultInstrument

    def getRegisteredInstruments(self):
        """Returns a list of registered intstrument names."""
        return self.getKeys()

    def registerInstrument(self, instrument):
        self.__defaultInstrument = instrument
        self.registerDataSeries(instrument)

    def getDataSeries(self, instrument=None):
        """Returns the :class:`pyalgotrade.dataseries.bards.BarDataSeries` for a given instrument.

        :param instrument: Instrument identifier. If None, the default instrument is returned.
        :type instrument: string.
        :rtype: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
        """
        if instrument is None:
            instrument = self.__defaultInstrument
        return self[instrument]


# This class is used by the optimizer module. The barfeed is already built on the server side, and the bars are sent back to workers.
class OptimizerBarFeed(BaseBarFeed):
    def __init__(self, frequency, instruments, bars, maxLen=dataseries.DEFAULT_MAX_LEN):
        BaseBarFeed.__init__(self, frequency, maxLen)
        for instrument in instruments:
            self.registerInstrument(instrument)
        self.__bars = bars
        self.__nextBar = 0
        try:
            self.__barsHaveAdjClose = self.__bars[0][instruments[0]].getAdjClose() is not None
        except Exception:
            self.__barsHaveAdjClose = False

    def barsHaveAdjClose(self):
        return self.__barsHaveAdjClose

    def isRealTime(self):
        return False

    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass

    def peekDateTime(self):
        self.__bars[self.__nextBar].getDateTime()

    def getNextBars(self):
        ret = None
        if self.__nextBar < len(self.__bars):
            ret = self.__bars[self.__nextBar]
            self.__nextBar += 1
        return ret

    def eof(self):
        return self.__nextBar >= len(self.__bars)
