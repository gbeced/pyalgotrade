import itertools
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.optimizer import server


def parameters_generator():
    instrument = ["dia"]
    entrySMA = range(150, 251)
    exitSMA = range(5, 16)
    rsiPeriod = range(2, 11)
    overBoughtThreshold = range(75, 96)
    overSoldThreshold = range(5, 26)
    return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)

# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the feed from the CSV files.
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV("dia", "dia-2009.csv")
    feed.addBarsFromCSV("dia", "dia-2010.csv")
    feed.addBarsFromCSV("dia", "dia-2011.csv")

    # Run the server.
    server.serve(feed, parameters_generator(), "localhost", 5000)
