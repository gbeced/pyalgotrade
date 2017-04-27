import itertools
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.optimizer import lowmemserver


def parameters_generator():
    instrument = ["dia"]
    entrySMA = range(150, 251)
    exitSMA = range(5, 16)
    rsiPeriod = range(2, 11)
    overBoughtThreshold = range(75, 96)
    overSoldThreshold = range(5, 26)
    return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod,
                             overBoughtThreshold, overSoldThreshold)


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the feed from the CSV files.
    feed = yahoofeed.Feed()

    # Notice how we can pass multiple intruments and multiple
    # files per instrument by using an array (iterable) of tuples.
    # It is important to pass files so that data is in chronological
    # order.
    lowmemserver.serveDataAndCode([("dia", "dia-2009.csv"),
                                   ("dia", "dia-2010.csv"),
                                   ("dia", "dia-2011.csv")],
                                  pickle.dumps(feed),
                                  parameters_generator(),
                                  "localhost",
                                  5000)
