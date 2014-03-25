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

from pyalgotrade import warninghelpers


class Frequency(object):
    """Enum like class for bar frequencies. Valid values are:

    * **Frequency.TRADE**: The bar represents a single trade.
    * **Frequency.SECOND**: The bar summarizes the trading activity during 1 second.
    * **Frequency.MINUTE**: The bar summarizes the trading activity during 1 minute.
    * **Frequency.HOUR**: The bar summarizes the trading activity during 1 hour.
    * **Frequency.DAY**: The bar summarizes the trading activity during 1 day.
    * **Frequency.WEEK**: The bar summarizes the trading activity during 1 week.
    """

    # It is important for frequency values to get bigger for bigger windows.
    TRADE = -1
    SECOND = 1
    MINUTE = 60
    HOUR = 60*60
    DAY = 24*60*60
    WEEK = 24*60*60*7


class Bar(object):
    """A Bar is a summary of the trading activity for a security in a given period.

    .. note::
        This is a base class and should not be used directly.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def getDateTime(self):
        """Returns the :class:`datetime.datetime`."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getOpen(self, adjusted=False):
        """Returns the opening price."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getHigh(self, adjusted=False):
        """Returns the highest price."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getLow(self, adjusted=False):
        """Returns the lowest price."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getClose(self, adjusted=False):
        """Returns the closing price."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getVolume(self):
        """Returns the volume."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getAdjClose(self):
        """Returns the adjusted closing price."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getFrequency(self):
        """The bar's period."""
        raise NotImplementedError()

    def getTypicalPrice(self):
        """Returns the typical price."""
        return (self.getHigh() + self.getLow() + self.getClose()) / 3.0


class BasicBar(Bar):
    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__open', '__close', '__high', '__low', '__volume', '__adjClose', '__frequency')

    def __init__(self, dateTime, open_, high, low, close, volume, adjClose, frequency):
        if high < open_:
            raise Exception("high < open on %s" % (dateTime))
        if high < low:
            raise Exception("high < low on %s" % (dateTime))
        if high < close:
            raise Exception("high < close on %s" % (dateTime))
        if low > open_:
            raise Exception("low > open on %s" % (dateTime))
        if low > high:
            raise Exception("low > high on %s" % (dateTime))
        if low > close:
            raise Exception("low > close on %s" % (dateTime))

        self.__dateTime = dateTime
        self.__open = open_
        self.__close = close
        self.__high = high
        self.__low = low
        self.__volume = volume
        self.__adjClose = adjClose
        self.__frequency = frequency

    def __setstate__(self, state):
        (self.__dateTime, self.__open, self.__close, self.__high, self.__low, self.__volume, self.__adjClose, self.__frequency) = state

    def __getstate__(self):
        return (self.__dateTime, self.__open, self.__close, self.__high, self.__low, self.__volume, self.__adjClose, self.__frequency)

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        if adjusted:
            if self.__adjClose is None:
                raise Exception("Adjusted close is missing")
            return self.__adjClose * self.__open / float(self.__close)
        else:
            return self.__open

    def getHigh(self, adjusted=False):
        if adjusted:
            if self.__adjClose is None:
                raise Exception("Adjusted close is missing")
            return self.__adjClose * self.__high / float(self.__close)
        else:
            return self.__high

    def getLow(self, adjusted=False):
        if adjusted:
            if self.__adjClose is None:
                raise Exception("Adjusted close is missing")
            return self.__adjClose * self.__low / float(self.__close)
        else:
            return self.__low

    def getClose(self, adjusted=False):
        if adjusted:
            if self.__adjClose is None:
                raise Exception("Adjusted close is missing")
            return self.__adjClose
        else:
            return self.__close

    def getVolume(self):
        return self.__volume

    def getAdjOpen(self):
        # Deprecated in 0.15
        warninghelpers.deprecation_warning("The getAdjOpen method will be deprecated in the next version. Please use the getOpen(True) instead.", stacklevel=2)
        return self.getOpen(True)

    def getAdjHigh(self):
        # Deprecated in 0.15
        warninghelpers.deprecation_warning("The getAdjHigh method will be deprecated in the next version. Please use the getHigh(True) instead.", stacklevel=2)
        return self.getHigh(True)

    def getAdjLow(self):
        # Deprecated in 0.15
        warninghelpers.deprecation_warning("The getAdjLow method will be deprecated in the next version. Please use the getLow(True) instead.", stacklevel=2)
        return self.getLow(True)

    def getAdjClose(self):
        return self.__adjClose

    def getFrequency(self):
        return self.__frequency


class Bars(object):
    """A group of :class:`Bar` objects.

    :param barDict: A map of instrument to :class:`Bar` objects.
    :type barDict: map.

    .. note::
        All bars must have the same datetime.
    """
    def __init__(self, barDict):
        if len(barDict) == 0:
            raise Exception("No bars supplied")

        # Check that bar datetimes are in sync
        firstDateTime = None
        firstInstrument = None
        for instrument, currentBar in barDict.iteritems():
            if firstDateTime is None:
                firstDateTime = currentBar.getDateTime()
                firstInstrument = instrument
            elif currentBar.getDateTime() != firstDateTime:
                raise Exception("Bar data times are not in sync. %s %s != %s %s" % (instrument, currentBar.getDateTime(), firstInstrument, firstDateTime))

        self.__barDict = barDict
        self.__dateTime = firstDateTime

    def __getitem__(self, instrument):
        """Returns the :class:`pyalgotrade.bar.Bar` for the given instrument. If the instrument is not found an exception is raised."""
        return self.__barDict[instrument]

    def __contains__(self, instrument):
        """Returns True if a :class:`pyalgotrade.bar.Bar` for the given instrument is available."""
        return instrument in self.__barDict

    def items(self):
        return self.__barDict.items()

    def keys(self):
        return self.__barDict.keys()

    def getInstruments(self):
        """Returns the instrument symbols."""
        return self.__barDict.keys()

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` for this set of bars."""
        return self.__dateTime

    def getBar(self, instrument):
        """Returns the :class:`pyalgotrade.bar.Bar` for the given instrument or None if the instrument is not found."""
        return self.__barDict.get(instrument, None)
