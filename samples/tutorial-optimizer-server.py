import itertools
from pyalgotrade.optimizer import server
from pyalgotrade.barfeed import quandlfeed


def parameters_generator():
    instrument = ["ibm"]
    entrySMA = range(150, 251)
    exitSMA = range(5, 16)
    rsiPeriod = range(2, 11)
    overBoughtThreshold = range(75, 96)
    overSoldThreshold = range(5, 26)
    return itertools.product(instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold, overSoldThreshold)


# The if __name__ == '__main__' part is necessary if running on Windows.
if __name__ == '__main__':
    # Load the bar feed from the CSV files.
    feed = quandlfeed.Feed()
    feed.addBarsFromCSV("ibm", "WIKI-IBM-2009-quandl.csv")
    feed.addBarsFromCSV("ibm", "WIKI-IBM-2010-quandl.csv")
    feed.addBarsFromCSV("ibm", "WIKI-IBM-2011-quandl.csv")

    # Run the server.
    server.serve(feed, parameters_generator(), "localhost", 5000)
