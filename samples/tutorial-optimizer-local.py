import itertools
from pyalgotrade.optimizer import local
from pyalgotrade.barfeed import yahoofeed
import rsi2


def parameters_generator():
    instrument = ["dia"]
    entrySMA = list(range(150, 251))
    exitSMA = list(range(5, 16))
    rsiPeriod = list(range(2, 11))
    overBoughtThreshold = list(range(75, 96))
    overSoldThreshold = list(range(5, 26))
    return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the feed from the CSV files.
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV("dia", "dia-2009.csv")
    feed.addBarsFromCSV("dia", "dia-2010.csv")
    feed.addBarsFromCSV("dia", "dia-2011.csv")

    local.run(rsi2.RSI2, feed, parameters_generator())
