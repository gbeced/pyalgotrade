import datetime

from pyalgotrade import strategy
from pyalgotrade.technical import roc
from pyalgotrade.technical import stats

# This strategy is inspired on: http://nobulart.com/bitcoin/blog/bitcoin-scalper-part-1/
# 
# Possible states and transitions:
#   NoPos -> WaitEntry
#   WaitEntry -> LongPos | NoPos
#   LongPos -> WaitExitLimit | WaitExitMarket
#   WaitExitLimit -> WaitExitMarket | NoPos
#   WaitExitMarket -> NoPos

class Strategy(strategy.BaseStrategy):
    def __init__(self, instrument, feed, brk):
        strategy.BaseStrategy.__init__(self, feed, brk)
        self.__verbosityLevel = 1
        self.__instrument = instrument
        self.__orderSize = 0.2
        self.__targetPricePct = 0.015
        self.__commitPricePct = self.__targetPricePct / 2
        self.__stopLossPct = -0.02
        # Time to wait for BUY order to get filled.
        self.__maxWaitEntry = datetime.timedelta(minutes=3)
        # Maximum holding period.
        self.__maxHoldPeriod = datetime.timedelta(hours=1)

        volatilityPeriod = 5 # How many returns to use to calculate volatility.
        self.returnsVolatility = stats.StdDev(roc.RateOfChange(feed[self.__instrument].getCloseDataSeries(), 1), volatilityPeriod)

        self.__switchNoPos()

    def setVerbosityLevel(self, level):
        self.__verbosityLevel = level

    def __log(self, level, *elements):
        if level >= self.__verbosityLevel:
            print " ".join([str(element) for element in elements])

    def __switchNoPos(self):
        self.__stateFun = self.__onNoPos
        self.__position = None
        self.__commitPrice = None
        self.__targetPrice = None
        self.__deadline = None

    def __exitWithMarketOrder(self, bars):
        # Exit with a market order at the target price and switch to WaitExitMarket
        self.__log(1, bars.getDateTime(), "SELL (Market order)")
        self.__position.exit()
        self.__stateFun = self.__onWaitExitMarket

    # Calculate the bid price based on the current price and the volatility.
    def __getBidPrice(self, currentPrice):
        vol = self.returnsVolatility[-1]
        if vol != None and vol > 0.006:
            return currentPrice * 0.98
        return None

    def onEnterOk(self, position):
        assert(self.__position == position)
        assert(self.__stateFun == self.__onWaitEntry)

        self.__log(1, position.getEntryOrder().getExecutionInfo().getDateTime(), "BUY filled at", position.getEntryOrder().getExecutionInfo().getPrice())

        # Switch to LongPos
        self.__deadline = position.getEntryOrder().getExecutionInfo().getDateTime() + self.__maxHoldPeriod
        self.__stateFun = self.__onLongPos

    def onEnterCanceled(self, position):
        assert(self.__position == position)
        assert(self.__stateFun == self.__onWaitEntry)

        self.__log(1, "BUY canceled.")

        # Switch to NoPos
        self.__switchNoPos()

    def onExitOk(self, position):
        assert(self.__position == position)
        assert(self.__stateFun in (self.__onWaitExitLimit, self.__onWaitExitMarket))

        self.__log(1, position.getExitOrder().getExecutionInfo().getDateTime(), "SELL filled. %", position.getReturn())

        # Switch to NoPos
        self.__switchNoPos()

    def onExitCanceled(self, position):
        assert(self.__position == position)
        assert(self.__stateFun in (self.__onWaitExitLimit, self.__onWaitExitMarket))

        self.__log(1, "SELL canceled. Resubmitting as market order.")

        # If the exit was canceled, re-submit it as a market order.
        self.__position.exit()
        self.__stateFun = self.__onWaitExitMarket

    def __waitingPeriodExceeded(self, currentDateTime):
        assert(self.__deadline != None)
        return currentDateTime >= self.__deadline

    def __stopLoss(self, currentPrice):
        assert(self.__position != None)
        return self.__position.getUnrealizedReturn(currentPrice) <= self.__stopLossPct

    # NoPos: A position is not opened.
    def __onNoPos(self, bars):
        assert(self.__position == None)
        assert(self.__commitPrice == None)
        assert(self.__targetPrice == None)

        currentPrice = bars[self.__instrument].getClose()
        bidPrice = self.__getBidPrice(currentPrice)
        if bidPrice != None:
            self.__commitPrice = bidPrice * (1 + self.__commitPricePct)
            self.__targetPrice = bidPrice * (1 + self.__targetPricePct)
            # EnterLong and switch state to WaitEntry
            self.__log(1, bars.getDateTime(), "BUY (ask: %s commit: %s target: %s)" % (bidPrice, self.__commitPrice, self.__targetPrice))
            self.__position = self.enterLongLimit(self.__instrument, bidPrice, self.__orderSize, True)
            self.__stateFun = self.__onWaitEntry
            self.__deadline = bars.getDateTime() + self.__maxWaitEntry

    # WaitEntry: Waiting for the entry order to get filled.
    def __onWaitEntry(self, bars):
        assert(self.__position != None)
        assert(not self.__position.entryFilled())

        if self.__waitingPeriodExceeded(bars.getDateTime()):
            # Cancel the entry order. This should eventually take us back to NoPos.
            self.__log(1, bars.getDateTime(), "Waiting period exceeded. Cancel entry")
            self.__position.cancelEntry()

    # LongPos: In a long position.
    def __onLongPos(self, bars):
        assert(self.__position != None)
        assert(self.__commitPrice != None)
        assert(self.__targetPrice != None)

        currentPrice = bars[self.__instrument].getClose()
        # If the holding perios is exceeded, we exit with a market order.
        if self.__waitingPeriodExceeded(bars.getDateTime()):
            self.__log(1, bars.getDateTime(), "Holding period exceeded.")
            self.__exitWithMarketOrder(bars)
        elif self.__stopLoss(currentPrice):
            self.__log(1, bars.getDateTime(), "Stop loss.")
            self.__exitWithMarketOrder(bars)
        elif currentPrice >= self.__commitPrice:
            # Exit with a limit order at the target price and switch to WaitExitLimit
            self.__log(1, bars.getDateTime(), "SELL (%s)" % (self.__targetPrice))
            self.__position.exit(self.__targetPrice)
            self.__stateFun = self.__onWaitExitLimit

    # WaitExitLimit: Waiting for the sell limit order to get filled.
    def __onWaitExitLimit(self, bars):
        assert(self.__position != None)

        if self.__position.exitActive():
            currentPrice = bars[self.__instrument].getClose()
            if self.__stopLoss(currentPrice):
                self.__log(1, bars.getDateTime(), "Stop loss. Canceling SELL (Limit order).")
                self.__position.cancelExit()
        else:
            self.__exitWithMarketOrder()

    # WaitExitMarket: Waiting for the sell market order to get filled.
    def __onWaitExitMarket(self, bars):
        assert(self.__position != None)

    def onBars(self, bars):
        self.__log(0, bars.getDateTime(), "Price:", bars[self.__instrument].getClose(), "Volume:", bars[self.__instrument].getVolume(), "Volatility:", self.returnsVolatility[-1])
        self.__stateFun(bars)

