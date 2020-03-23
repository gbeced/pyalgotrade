from pyalgotrade import strategy
from pyalgotrade.barfeed import quandlfeed


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, priceCurrency):
        super(MyStrategy, self).__init__(feed, balances={})
        self.__instrument = instrument
        self.__priceCurrency = priceCurrency

    def onBars(self, bars):
        bar = bars.getBar(self.__instrument, self.__priceCurrency)
        self.info(bar.getClose())

# Load the bar feed from the CSV file
feed = quandlfeed.Feed()
feed.addBarsFromCSV("orcl", "USD", "WIKI-ORCL-2000-quandl.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, "orcl", "USD")
myStrategy.run()
