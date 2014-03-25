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

import datetime

from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade import barfeed


class TradeBar(bar.Bar):
    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__tradeId', '__price', '__amount')

    def __init__(self, dateTime, trade):
        self.__dateTime = dateTime
        self.__tradeId = trade.getId()
        self.__price = trade.getPrice()
        self.__amount = trade.getAmount()

    def __setstate__(self, state):
        (self.__dateTime, self.__tradeId, self.__price, self.__amount) = state

    def __getstate__(self):
        return (self.__dateTime, self.__tradeId, self.__price, self.__amount)

    def getTradeId(self):
        return self.__tradeId

    def getFrequency(self):
        return bar.Frequency.TRADE

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        return self.__price

    def getHigh(self, adjusted=False):
        return self.__price

    def getLow(self, adjusted=False):
        return self.__price

    def getClose(self, adjusted=False):
        return self.__price

    def getVolume(self):
        return self.__amount

    def getAdjClose(self):
        return None

    def getTypicalPrice(self):
        return self.__price


class LiveTradeFeed(barfeed.BaseBarFeed):
    """A real-time BarFeed that builds bars from live trades.

    :param client: A Bitstamp client.
    :type client: :class:`pyalgotrade.bitstamp.client.Client`.
    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.

    .. note::
        Note that a Bar will be created for every trade, so open, high, low and close values will all be the same.
    """

    def __init__(self, client, maxLen=dataseries.DEFAULT_MAX_LEN):
        barfeed.BaseBarFeed.__init__(self, bar.Frequency.TRADE, maxLen)
        self.__barDicts = []
        self.registerInstrument("BTC")
        client.getTradeEvent().subscribe(self.__onTrade)
        self.__prevTradeDateTime = None

    def isRealTime(self):
        return True

    # Bar datetimes should not duplicate. In case trade object datetimes conflict, we just move one slightly forward.
    def __getTradeDateTime(self, trade):
        ret = trade.getDateTime()
        if ret == self.__prevTradeDateTime:
            ret += datetime.timedelta(microseconds=1)
        self.__prevTradeDateTime = ret
        return ret

    def __onTrade(self, trade):
        # Build a bar for each trade.
        barDict = {
            "BTC": TradeBar(self.__getTradeDateTime(trade), trade)
            }
        self.__barDicts.append(barDict)

        # Dispatch immediately
        self.dispatch()

    def barsHaveAdjClose(self):
        return False

    def getNextBars(self):
        ret = None
        if len(self.__barDicts):
            ret = bar.Bars(self.__barDicts.pop(0))
        return ret

    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    def eof(self):
        return len(self.__barDicts) == 0

    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass
