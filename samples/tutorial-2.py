from pyalgotrade import strategy
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.technical import ma

class MyStrategy(strategy.Strategy):
    def __init__(self, feed):
        strategy.Strategy.__init__(self, feed)
        # We want a 15 period SMA over the closing prices.
        self.__sma = ma.SMA(feed.getDataSeries("orcl").getCloseDataSeries(), 15)

    def onBars(self, bars):
        bar = bars.getBar("orcl")
        print "%s: %s %s" % (bar.getDateTime(), bar.getClose(), self.__sma.getValue())

# Load the yahoo feed from the CSV file
feed = csvfeed.YahooFeed()
feed.addBarsFromCSV("orcl", "orcl-2000.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed)
myStrategy.run()

