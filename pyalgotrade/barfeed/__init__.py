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

from pyalgotrade import bar
from pyalgotrade.dataseries import bards
from pyalgotrade import feed
from pyalgotrade import dispatchprio


# This is only for backward compatibility since Frequency used to be defined here and not in bar.py.
Frequency = bar.Frequency


class BaseBarFeed(feed.BaseFeed):
    """Base class for :class:`pyalgotrade.bar.Bar` providing feeds.

    :param frequency: The bars frequency. Valid values defined in :class:`pyalgotrade.bar.Frequency`.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, frequency, maxLen=None):
        super(BaseBarFeed, self).__init__(maxLen)
        self.__frequency = frequency
        self.__useAdjustedValues = False
        self.__currentBars = None
        self.__lastBars = {}

    # Return the datetime for the current bars.
    @abc.abstractmethod
    def getCurrentDateTime(self):
        raise NotImplementedError()

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

    ## BEGIN feed.BaseFeed abstractmethods
    def createDataSeries(self, key, maxLen):
        instrument, priceCurrency = bar.key_to_pair(key)
        ret = bards.BarDataSeries(instrument, priceCurrency, maxLen)
        ret.setUseAdjustedValues(self.__useAdjustedValues)
        return ret

    def getNextValues(self):
        dateTime = None
        bars = self.getNextBars()
        if bars is not None:
            dateTime = bars.getDateTime()

            # Check that current bar datetimes are greater than the previous one.
            if self.__currentBars is not None and self.__currentBars.getDateTime() >= dateTime:
                raise Exception(
                    "Bar date times are not in order. Previous datetime was %s and current datetime is %s" % (
                        self.__currentBars.getDateTime(),
                        dateTime
                    )
                )

            # Update self.__currentBars and self.__lastBars
            self.__currentBars = bars
            for bar in bars:
                self.__lastBars[bar.pairToKey()] = bar
        return (dateTime, bars)
    ## END feed.BaseFeed abstractmethods

    def reset(self):
        self.__currentBars = None
        self.__lastBars = {}
        super(BaseBarFeed, self).reset()

    def setUseAdjustedValues(self, useAdjusted):
        if useAdjusted and not self.barsHaveAdjClose():
            raise Exception("The barfeed doesn't support adjusted close values")
        # This is to affect future dataseries when they get created.
        self.__useAdjustedValues = useAdjusted
        # Update underlying dataseries
        for ds in self.getAllDataSeries():
            ds.setUseAdjustedValues(useAdjusted)

    def getFrequency(self):
        return self.__frequency

    def isIntraday(self):
        return self.__frequency < bar.Frequency.DAY

    def getCurrentBars(self):
        """Returns the current :class:`pyalgotrade.bar.Bars`."""
        return self.__currentBars

    def getLastBar(self, instrument, priceCurrency):
        """
        Returns the last :class:`pyalgotrade.bar.Bar` for a given instrument and price currency, or None.
        """
        return self.__lastBars.get(bar.pair_to_key(instrument, priceCurrency))

    def getDataSeries(self, instrument, priceCurrency):
        """
        Returns the :class:`pyalgotrade.dataseries.bards.BarDataSeries` for a given instrument and price currency or
        None if it was not found.

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param instrument: The price currency.
        :type instrument: string.
        :rtype: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
        """
        return super(BaseBarFeed, self).getDataSeries(bar.pair_to_key(instrument, priceCurrency))

    def getDispatchPriority(self):
        return dispatchprio.BAR_FEED


# This class is used by the optimizer module. The barfeed is already built on the server side,
# and the bars are sent back to workers.
class OptimizerBarFeed(BaseBarFeed):
    def __init__(self, frequency, pairs, bars, maxLen=None):
        super(OptimizerBarFeed, self).__init__(frequency, maxLen)
        for pair in pairs:
            self.registerDataSeries(pair)
        self.__bars = bars
        self.__nextPos = 0
        self.__currDateTime = None

        # Check if bars have adjusted close.
        self.__barsHaveAdjClose = False
        for item in bars:
            for bar in item:
                self.__barsHaveAdjClose = bar.getAdjClose() is not None
                break
            break

    ## BEGIN observer.Subject abstractmethods
    def start(self):
        super(OptimizerBarFeed, self).start()

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        return self.__nextPos >= len(self.__bars)

    def peekDateTime(self):
        ret = None
        if self.__nextPos < len(self.__bars):
            ret = self.__bars[self.__nextPos].getDateTime()
        return ret
    ## END observer.Subject abstractmethods

    ## BEGIN BaseBarFeed abstractmethods
    def getCurrentDateTime(self):
        return self.__currDateTime

    def barsHaveAdjClose(self):
        return self.__barsHaveAdjClose

    def getNextBars(self):
        ret = None
        if self.__nextPos < len(self.__bars):
            ret = self.__bars[self.__nextPos]
            self.__currDateTime = ret.getDateTime()
            self.__nextPos += 1
        return ret
    ## END BaseBarFeed abstractmethods

