from pyalgotrade import strategy
from pyalgotrade.barfeed import quandlfeed
from pyalgotrade.technical import ma


def safe_round(value, digits):
    if value is not None:
        value = round(value, digits)
    return value


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument):
        super(MyStrategy, self).__init__(feed, balances={})
        # We want a 15 period SMA over the closing prices.
        self.__sma = ma.SMA(feed.getDataSeries(instrument).getCloseDataSeries(), 15)
        self.__instrument = instrument

    def onBars(self, bars):
        bar = bars.getBar(self.__instrument)
        self.info("%s %s" % (bar.getClose(), safe_round(self.__sma[-1], 2)))


# Load the bar feed from the CSV file
feed = quandlfeed.Feed()
feed.addBarsFromCSV("ORCL/USD", "WIKI-ORCL-2000-quandl.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, "ORCL/USD")
myStrategy.run()
