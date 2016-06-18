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

import math

from pyalgotrade import stratanalyzer
from pyalgotrade import observer
from pyalgotrade import dataseries


# Helper class to calculate time-weighted returns in a portfolio.
# Check http://www.wikinvest.com/wiki/Time-weighted_return
class TimeWeightedReturns(object):
    def __init__(self, initialValue):
        self.__lastValue = initialValue
        self.__flows = 0.0
        self.__lastPeriodRet = 0.0
        self.__cumRet = 0.0

    def deposit(self, amount):
        self.__flows += amount

    def withdraw(self, amount):
        self.__flows -= amount

    def getCurrentValue(self):
        return self.__lastValue

    # Update the value of the portfolio.
    def update(self, currentValue):
        if self.__lastValue:
            retSubperiod = (currentValue - self.__lastValue - self.__flows) / float(self.__lastValue)
        else:
            retSubperiod = 0.0

        self.__cumRet = (1 + self.__cumRet) * (1 + retSubperiod) - 1
        self.__lastPeriodRet = retSubperiod
        self.__lastValue = currentValue
        self.__flows = 0.0

    def getLastPeriodReturns(self):
        return self.__lastPeriodRet

    # Note that this value is not annualized.
    def getCumulativeReturns(self):
        return self.__cumRet


# Helper class to calculate PnL and returns over a single instrument (not the whole portfolio).
class PositionTracker(object):
    def __init__(self, instrumentTraits):
        self.__instrumentTraits = instrumentTraits
        self.reset()

    def reset(self):
        self.__pnl = 0.0
        self.__avgPrice = 0.0  # Volume weighted average price per share.
        self.__position = 0.0
        self.__commissions = 0.0
        self.__totalCommited = 0.0  # The total amount commited to this position.

    def getPosition(self):
        return self.__position

    def getAvgPrice(self):
        return self.__avgPrice

    def getCommissions(self):
        return self.__commissions

    def getPnL(self, price=None, includeCommissions=True):
        """
        Return the PnL that would result if closing the position a the given price.
        Note that this will be different if commissions are used when the trade is executed.
        """

        ret = self.__pnl
        if price:
            ret += (price - self.__avgPrice) * self.__position
        if includeCommissions:
            ret -= self.__commissions
        return ret

    def getReturn(self, price=None, includeCommissions=True):
        ret = 0
        pnl = self.getPnL(price=price, includeCommissions=includeCommissions)
        if self.__totalCommited != 0:
            ret = pnl / float(self.__totalCommited)
        return ret

    def __openNewPosition(self, quantity, price):
        self.__avgPrice = price
        self.__position = quantity
        self.__totalCommited = self.__avgPrice * abs(self.__position)

    def __extendCurrentPosition(self, quantity, price):
        newPosition = self.__instrumentTraits.roundQuantity(self.__position + quantity)
        self.__avgPrice = (self.__avgPrice*abs(self.__position) + price*abs(quantity)) / abs(float(newPosition))
        self.__position = newPosition
        self.__totalCommited = self.__avgPrice * abs(self.__position)

    def __reduceCurrentPosition(self, quantity, price):
        # Check that we're closing or reducing partially
        assert self.__instrumentTraits.roundQuantity(abs(self.__position) - abs(quantity)) >= 0
        pnl = (price - self.__avgPrice) * quantity * -1

        self.__pnl += pnl
        self.__position = self.__instrumentTraits.roundQuantity(self.__position + quantity)
        if self.__position == 0:
            self.__avgPrice = 0.0

    def update(self, quantity, price, commission):
        assert quantity != 0, "Invalid quantity"
        assert price > 0, "Invalid price"
        assert commission >= 0, "Invalid commission"

        if self.__position == 0:
            self.__openNewPosition(quantity, price)
        else:
            # Are we extending the current position or going in the opposite direction ?
            currPosDirection = math.copysign(1, self.__position)
            tradeDirection = math.copysign(1, quantity)

            if currPosDirection == tradeDirection:
                self.__extendCurrentPosition(quantity, price)
            else:
                # If we're going in the opposite direction we could be:
                # 1: Partially reducing the current position.
                # 2: Completely closing the current position.
                # 3: Completely closing the current position and opening a new one in the opposite direction.
                if abs(quantity) <= abs(self.__position):
                    self.__reduceCurrentPosition(quantity, price)
                else:
                    newPos = self.__position + quantity
                    self.__reduceCurrentPosition(self.__position*-1, price)
                    self.__openNewPosition(newPos, price)

        self.__commissions += commission

    def buy(self, quantity, price, commission=0.0):
        assert quantity > 0, "Invalid quantity"
        self.update(quantity, price, commission)

    def sell(self, quantity, price, commission=0.0):
        assert quantity > 0, "Invalid quantity"
        self.update(quantity * -1, price, commission)


class ReturnsAnalyzerBase(stratanalyzer.StrategyAnalyzer):
    def __init__(self):
        super(ReturnsAnalyzerBase, self).__init__()
        self.__event = observer.Event()
        self.__portfolioReturns = None

    @classmethod
    def getOrCreateShared(cls, strat):
        name = cls.__name__
        # Get or create the shared ReturnsAnalyzerBase.
        ret = strat.getNamedAnalyzer(name)
        if ret is None:
            ret = ReturnsAnalyzerBase()
            strat.attachAnalyzerEx(ret, name)
        return ret

    def attached(self, strat):
        self.__portfolioReturns = TimeWeightedReturns(strat.getBroker().getEquity())

    # An event will be notified when return are calculated at each bar. The hander should receive 1 parameter:
    # 1: The current datetime.
    # 2: This analyzer's instance
    def getEvent(self):
        return self.__event

    def getNetReturn(self):
        return self.__portfolioReturns.getLastPeriodReturns()

    def getCumulativeReturn(self):
        return self.__portfolioReturns.getCumulativeReturns()

    def beforeOnBars(self, strat, bars):
        self.__portfolioReturns.update(strat.getBroker().getEquity())

        # Notify that new returns are available.
        self.__event.emit(bars.getDateTime(), self)


class Returns(stratanalyzer.StrategyAnalyzer):
    """
    A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates time-weighted returns for the
    whole portfolio.

    :param maxLen: The maximum number of values to hold in net and cumulative returs dataseries.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, maxLen=None):
        super(Returns, self).__init__()
        self.__netReturns = dataseries.SequenceDataSeries(maxLen=maxLen)
        self.__cumReturns = dataseries.SequenceDataSeries(maxLen=maxLen)

    def beforeAttach(self, strat):
        # Get or create a shared ReturnsAnalyzerBase
        analyzer = ReturnsAnalyzerBase.getOrCreateShared(strat)
        analyzer.getEvent().subscribe(self.__onReturns)

    def __onReturns(self, dateTime, returnsAnalyzerBase):
        self.__netReturns.appendWithDateTime(dateTime, returnsAnalyzerBase.getNetReturn())
        self.__cumReturns.appendWithDateTime(dateTime, returnsAnalyzerBase.getCumulativeReturn())

    def getReturns(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the returns for each bar."""
        return self.__netReturns

    def getCumulativeReturns(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the cumulative returns for each bar."""
        return self.__cumReturns
