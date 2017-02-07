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

from pyalgotrade import stratanalyzer

import datetime


class DrawDownHelper(object):
    def __init__(self):
        self.__highWatermark = None
        self.__lowWatermark = None
        self.__lastLow = None
        self.__highDateTime = None
        self.__lastDateTime = None

    # The drawdown duration, not necessarily the max drawdown duration.
    def getDuration(self):
        return self.__lastDateTime - self.__highDateTime

    def getMaxDrawDown(self):
        return (self.__lowWatermark - self.__highWatermark) / float(self.__highWatermark)

    def getCurrentDrawDown(self):
        return (self.__lastLow - self.__highWatermark) / float(self.__highWatermark)

    def update(self, dateTime, low, high):
        assert(low <= high)
        self.__lastLow = low
        self.__lastDateTime = dateTime

        if self.__highWatermark is None or high >= self.__highWatermark:
            self.__highWatermark = high
            self.__lowWatermark = low
            self.__highDateTime = dateTime
        else:
            self.__lowWatermark = min(self.__lowWatermark, low)


class DrawDown(stratanalyzer.StrategyAnalyzer):
    """A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates
    max. drawdown and longest drawdown duration for the portfolio."""

    def __init__(self):
        super(DrawDown, self).__init__()
        self.__maxDD = 0
        self.__longestDDDuration = datetime.timedelta()
        self.__currDrawDown = DrawDownHelper()

    def calculateEquity(self, strat):
        return strat.getBroker().getEquity()
        # ret = strat.getBroker().getCash()
        # for instrument, shares in strat.getBroker().getPositions().iteritems():
        #     _bar = strat.getFeed().getLastBar(instrument)
        #     if shares > 0:
        #         ret += strat.getBroker().getBarLow(_bar) * shares
        #     elif shares < 0:
        #         ret += strat.getBroker().getBarHigh(_bar) * shares
        # return ret

    def beforeOnBars(self, strat, bars):
        equity = self.calculateEquity(strat)
        self.__currDrawDown.update(bars.getDateTime(), equity, equity)
        self.__longestDDDuration = max(self.__longestDDDuration, self.__currDrawDown.getDuration())
        self.__maxDD = min(self.__maxDD, self.__currDrawDown.getMaxDrawDown())

    def getMaxDrawDown(self):
        """Returns the max. (deepest) drawdown."""
        return abs(self.__maxDD)

    def getLongestDrawDownDuration(self):
        """Returns the duration of the longest drawdown.

        :rtype: :class:`datetime.timedelta`.

        .. note::
            Note that this is the duration of the longest drawdown, not necessarily the deepest one.
        """
        return self.__longestDDDuration
