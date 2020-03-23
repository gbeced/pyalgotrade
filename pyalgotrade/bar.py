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

import abc

import six


PAIR_KEY_SEP = "/"


def pair_to_key(instrument, priceCurrency):
    ret = "%s%s%s" % (instrument, PAIR_KEY_SEP, priceCurrency)
    assert ret.count(PAIR_KEY_SEP) == 1, "Either instrument or priceCurrency contains %s" % PAIR_KEY_SEP
    return ret


def key_to_pair(pair):
    ret = pair.split(PAIR_KEY_SEP)
    assert len(ret) == 2
    return ret[0], ret[1]


class Frequency(object):

    """Enum like class for bar frequencies. Valid values are:

    * **Frequency.TRADE**: The bar represents a single trade.
    * **Frequency.SECOND**: The bar summarizes the trading activity during 1 second.
    * **Frequency.MINUTE**: The bar summarizes the trading activity during 1 minute.
    * **Frequency.HOUR**: The bar summarizes the trading activity during 1 hour.
    * **Frequency.DAY**: The bar summarizes the trading activity during 1 day.
    * **Frequency.WEEK**: The bar summarizes the trading activity during 1 week.
    * **Frequency.MONTH**: The bar summarizes the trading activity during 1 month.
    """

    # It is important for frequency values to get bigger for bigger windows.
    TRADE = -1
    SECOND = 1
    MINUTE = 60
    HOUR = 60*60
    DAY = 24*60*60
    WEEK = 24*60*60*7
    MONTH = 24*60*60*31


@six.add_metaclass(abc.ABCMeta)
class Bar(object):

    """A Bar is a summary of the trading activity in a given period.

    .. note::
        This is a base class and should not be used directly.
    """

    @abc.abstractmethod
    def getDateTime(self):
        """Returns the :class:`datetime.datetime`."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getFrequency(self):
        """The bar's period."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getInstrument(self):
        """
        Returns the instrument.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def getPriceCurrency(self):
        """
        Returns the price currency.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def setUseAdjustedValue(self, useAdjusted):
        raise NotImplementedError()

    @abc.abstractmethod
    def getUseAdjValue(self):
        """Returns True if the adjusted close value will be returned when getPrice is called."""
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

    def getTypicalPrice(self):
        """Returns the typical price."""
        return (self.getHigh() + self.getLow() + self.getClose()) / 3.0

    @abc.abstractmethod
    def getPrice(self):
        """Returns the closing or adjusted closing price."""
        raise NotImplementedError()

    def getExtraColumns(self):
        return {}

    def pairToKey(self):
        return pair_to_key(self.getInstrument(), self.getPriceCurrency())


class BasicBar(Bar):
    # Optimization to reduce memory footprint.
    __slots__ = (
        '__instrument',
        '__priceCurrency',
        '__dateTime',
        '__open',
        '__close',
        '__high',
        '__low',
        '__volume',
        '__adjClose',
        '__frequency',
        '__useAdjustedValue',
        '__extra',
    )

    def __init__(
        self, instrument, priceCurrency, dateTime, open_, high, low, close, volume, adjClose, frequency, extra={}
    ):
        if high < low:
            raise Exception("high < low on %s" % (dateTime))
        elif high < open_:
            raise Exception("high < open on %s" % (dateTime))
        elif high < close:
            raise Exception("high < close on %s" % (dateTime))
        elif low > open_:
            raise Exception("low > open on %s" % (dateTime))
        elif low > close:
            raise Exception("low > close on %s" % (dateTime))

        self.__instrument = instrument
        self.__priceCurrency = priceCurrency
        self.__dateTime = dateTime
        self.__open = open_
        self.__close = close
        self.__high = high
        self.__low = low
        self.__volume = volume
        self.__adjClose = adjClose
        self.__frequency = frequency
        self.__useAdjustedValue = False
        self.__extra = extra

    def __setstate__(self, state):
        (self.__instrument,
            self.__priceCurrency,
            self.__dateTime,
            self.__open,
            self.__close,
            self.__high,
            self.__low,
            self.__volume,
            self.__adjClose,
            self.__frequency,
            self.__useAdjustedValue,
            self.__extra) = state

    def __getstate__(self):
        return (
            self.__instrument,
            self.__priceCurrency,
            self.__dateTime,
            self.__open,
            self.__close,
            self.__high,
            self.__low,
            self.__volume,
            self.__adjClose,
            self.__frequency,
            self.__useAdjustedValue,
            self.__extra
        )

    def getInstrument(self):
        return self.__instrument

    def getPriceCurrency(self):
        return self.__priceCurrency

    def setUseAdjustedValue(self, useAdjusted):
        if useAdjusted and self.__adjClose is None:
            raise Exception("Adjusted close is not available")
        self.__useAdjustedValue = useAdjusted

    def getUseAdjValue(self):
        return self.__useAdjustedValue

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

    def getAdjClose(self):
        return self.__adjClose

    def getFrequency(self):
        return self.__frequency

    def getPrice(self):
        if self.__useAdjustedValue:
            return self.__adjClose
        else:
            return self.__close

    def getExtraColumns(self):
        return self.__extra


class Bars(object):

    """
    A group of :class:`Bar` objects with the same datetime.

    :param bars: A list of :class:`Bar` objects.
    :type bars: list.

    .. note::
        All bars must have the same datetime.
    """

    def __init__(self, bars):
        assert isinstance(bars, list), "Invalid type for bars. Must be a list"

        if len(bars) == 0:
            raise Exception("No bars supplied")

        self.__barDict = {}

        # Check that bar datetimes are in sync
        firstDateTime = None
        firstInstrument = None
        for currentBar in bars:
            if firstDateTime is None:
                firstDateTime = currentBar.getDateTime()
                firstInstrument = currentBar.getInstrument()
            elif currentBar.getDateTime() != firstDateTime:
                raise Exception("Bar data times are not in sync. %s %s != %s %s" % (
                    currentBar.getInstrument(),
                    currentBar.getDateTime(),
                    firstInstrument,
                    firstDateTime
                ))

            pair = currentBar.pairToKey()
            assert pair not in self.__barDict, "Duplicate bars %s" % pair
            self.__barDict[pair] = currentBar

        self.__dateTime = firstDateTime

    def __getitem__(self, pair):
        """
        Returns the :class:`pyalgotrade.bar.Bar` for a given pair in this format: INSTRUMENT/PRICE_CURRENCY.
        If the pair is not found an exception is raised.
        """
        return self.__barDict[pair]

    def __contains__(self, pair):
        """Returns True if a :class:`pyalgotrade.bar.Bar` for the given pair is available."""
        return pair in self.__barDict

    def __iter__(self):
        return iter(self.__barDict.values())

    def items(self):
        return list(self.__barDict.items())

    def getPairs(self):
        """Returns the pairs in this format: INSTRUMENT/PRICE_CURRENCY."""
        return list(self.__barDict.keys())

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` for this set of bars."""
        return self.__dateTime

    def getBar(self, instrument, priceCurrency):
        """
        Returns the :class:`pyalgotrade.bar.Bar` for the given instrument and price currency or None if it is not found.
        """
        return self.__barDict.get("%s/%s" % (instrument, priceCurrency))

    def getBars(self):
        """
        Returns all :class:`pyalgotrade.bar.Bar`.
        """
        return list(self.__barDict.values())
