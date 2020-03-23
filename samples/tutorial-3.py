from pyalgotrade import strategy
from pyalgotrade.barfeed import quandlfeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi


def safe_round(value, digits):
    if value is not None:
        value = round(value, digits)
    return value


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, priceCurrency):
        super(MyStrategy, self).__init__(feed, balances={})
        self.__rsi = rsi.RSI(feed.getDataSeries(instrument, priceCurrency).getCloseDataSeries(), 14)
        self.__sma = ma.SMA(self.__rsi, 15)
        self.__instrument = instrument
        self.__priceCurrency = priceCurrency

    def onBars(self, bars):
        bar = bars.getBar(self.__instrument, self.__priceCurrency)
        self.info("%s %s %s" % (
            bar.getClose(), safe_round(self.__rsi[-1], 2), safe_round(self.__sma[-1], 2)
        ))


# Load the bar feed from the CSV file
feed = quandlfeed.Feed()
feed.addBarsFromCSV("orcl", "USD", "WIKI-ORCL-2000-quandl.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, "orcl", "USD")
myStrategy.run()
