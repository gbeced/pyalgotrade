from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

class Strategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod, cash=1000):
        strategy.BacktestingStrategy.__init__(self, feed, cash)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.getBroker().setUseAdjustedValues(True)
        self.__adjClose = feed[instrument].getAdjCloseDataSeries()
        self.__sma = ma.SMA(self.__adjClose, smaPeriod)

    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exit()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__position == None:
            if cross.cross_above(self.__adjClose, self.__sma) > 0:
                # Enter a buy market order for 10 shares. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, 10, True)
        # Check if we have to exit the position.
        elif cross.cross_below(self.__adjClose, self.__sma) > 0:
             self.__position.exit()

