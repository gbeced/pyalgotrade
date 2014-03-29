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

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi


class Strategy(strategy.BacktestingStrategy):
    def __init__(self, feed, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
        initialCash = 2000
        strategy.BacktestingStrategy.__init__(self, feed, initialCash)
        self.__instrument = feed.getDefaultInstrument()
        ds = feed.getDataSeries().getCloseDataSeries()
        self.__entrySMA = ma.SMA(ds, entrySMA)
        self.__exitSMA = ma.SMA(ds, exitSMA)
        self.__rsi = rsi.RSI(ds, rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold
        self.__longPos = None
        self.__shortPos = None

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitOk(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
            return

        bar = bars.getBar(self.__instrument)
        if self.__longPos is not None:
            if self.exitLongSignal(bar):
                self.__longPos.exitMarket()
        elif self.__shortPos is not None:
            if self.exitShortSignal(bar):
                self.__shortPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                self.__longPos = self.enterLong(self.__instrument, 10, True)
            elif self.enterShortSignal(bar):
                self.__shortPos = self.enterShort(self.__instrument, 10, True)

    def enterLongSignal(self, bar):
        return bar.getClose() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold

    def exitLongSignal(self, bar):
        return bar.getClose() > self.__exitSMA[-1]

    def enterShortSignal(self, bar):
        return bar.getClose() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def exitShortSignal(self, bar):
        return bar.getClose() < self.__exitSMA[-1]
