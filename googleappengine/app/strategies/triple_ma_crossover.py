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


class Strategy(strategy.BacktestingStrategy):
    def __init__(self, feed, ema1, ema2, ema3, ema4, daysToHold):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = feed.getDefaultInstrument()
        self.__daysToHold = daysToHold
        ds = feed[self.__instrument].getCloseDataSeries()
        self.__ema1 = ma.EMA(ds, ema1)
        self.__ema2 = ma.EMA(ds, ema2)
        self.__ema3 = ma.EMA(ds, ema3)
        self.__ema4 = ma.EMA(ds, ema4)
        self.__daysLeft = 0
        self.__position = None

    def getEMA1(self):
        return self.__ema1

    def getEMA2(self):
        return self.__ema2

    def getEMA3(self):
        return self.__ema3

    def getEMA4(self):
        return self.__ema4

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def __getOrderSize(self, price):
        cash = self.getBroker().getCash() * 0.9
        return int(cash / price)

    def __entrySignal(self, bars):
        ret = False

        try:
            ema1 = self.__ema1[-1]
            ema2 = self.__ema2[-1]
            ema3 = self.__ema3[-1]
            ema4 = self.__ema4[-1]
            close3DaysAgo = self.getFeed()[self.__instrument][-3].getClose()
            close5DaysAgo = self.getFeed()[self.__instrument][-5].getClose()

            # Check that we have all the EMAs available.
            if ema1 is None or ema2 is None or ema3 is None or ema4 is None:
                return False

            openPrice = bars[self.__instrument].getOpen()
            closePrice = bars[self.__instrument].getClose()

            # Opens below the moving averages:
            ret = openPrice < ema3
            ret = ret and openPrice < ema2
            ret = ret and openPrice < ema1
            # Closes above the moving averages
            ret = ret and closePrice > ema3
            ret = ret and closePrice > ema1
            ret = ret and closePrice > ema2
            ret = ret and closePrice > openPrice
            # Whipsaw protection, this part tries to ensure that the price is moving in the right direction.
            ret = ret and close3DaysAgo < ema3
            ret = ret and close5DaysAgo < close3DaysAgo
            ret = ret and close5DaysAgo < ema4
        except IndexError:
            pass

        return ret

    def onBars(self, bars):
        closePrice = bars[self.__instrument].getClose()
        if self.__position is not None:
            self.__daysLeft -= 1
            if self.__daysLeft <= 0:
                self.__position.exitMarket()
            elif self.__position.getUnrealizedReturn() < -0.03:
                self.__position.exitMarket()
        elif self.__entrySignal(bars):
            self.__position = self.enterLong(self.__instrument, self.__getOrderSize(closePrice))
            self.__daysLeft = self.__daysToHold
