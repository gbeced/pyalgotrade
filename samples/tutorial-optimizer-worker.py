from pyalgotrade.optimizer import worker
from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi

class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold):
        strategy.BacktestingStrategy.__init__(self, feed, 2000)
        ds = feed["dia"].getCloseDataSeries()
        self.__entrySMA = ma.SMA(ds, entrySMA)
        self.__exitSMA = ma.SMA(ds, exitSMA)
        self.__rsi = rsi.RSI(ds, rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold
        self.__longPos = None
        self.__shortPos = None

    def onEnterOk(self, position):
        pass

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
        position.exit()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
            return

        bar = bars["dia"]
        if self.__longPos != None:
            if self.exitLongSignal(bar):
                self.__longPos.exit()
        elif self.__shortPos != None:
            if self.exitShortSignal(bar):
                self.__shortPos.exit()
        else:
            if self.enterLongSignal(bar):
                self.__longPos = self.enterLong("dia", 10, True)
            elif self.enterShortSignal(bar):
                self.__shortPos = self.enterShort("dia", 10, True)

    def enterLongSignal(self, bar):
        return bar.getClose() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold

    def exitLongSignal(self, bar):
        return bar.getClose() > self.__exitSMA[-1]

    def enterShortSignal(self, bar):
        return bar.getClose() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def exitShortSignal(self, bar):
        return bar.getClose() < self.__exitSMA[-1]

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    worker.run(MyStrategy, "localhost", 5000, workerName="localworker")

