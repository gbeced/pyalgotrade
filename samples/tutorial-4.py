from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma

class MyStrategy(strategy.Strategy):
    def __init__(self, feed, instrument, smaPeriod):
        strategy.Strategy.__init__(self, feed, 1000)
        self.__sma = ma.SMA(feed[instrument].getCloseDataSeries(), smaPeriod)
        self.__position = None
        self.__instrument = instrument

    def onStart(self):
        print "Initial portfolio value: $%.2f" % self.getBroker().getEquity()

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        print "%s: BUY at $%.2f" % (execInfo.getDateTime(), execInfo.getPrice())

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        print "%s: SELL at $%.2f" % (execInfo.getDateTime(), execInfo.getPrice())
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.exitPosition(self.__position)

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if self.__sma[-1] is None:
            return

        bar = bars[self.__instrument]
        # If a position was not opened, check if we should enter a long position.
        if self.__position == None:
            if bar.getClose() > self.__sma[-1]:
                # Enter a buy market order for 10 shares. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, 10, True)
        # Check if we have to exit the position.
        elif bar.getClose() < self.__sma[-1]:
             self.exitPosition(self.__position)

    def onFinish(self, bars):
        print "Final portfolio value: $%.2f" % self.getBroker().getEquity()

def run_strategy(smaPeriod):
    # Load the yahoo feed from the CSV file
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV("orcl", "orcl-2000.csv")

    # Evaluate the strategy with the feed's bars.
    myStrategy = MyStrategy(feed, "orcl", smaPeriod)
    myStrategy.run()

run_strategy(15)

