from pyalgotrade import strategy
from pyalgotrade.mtgox import barfeed

class MyStrategy(strategy.Strategy):
    def onBars(self, bars):
        bar = bars["BTC"]
        print "%s: %s %s" % (bar.getDateTime(), bar.getClose(), bar.getVolume())

# Load the trades from the CSV file
feed = barfeed.TradesCSVFeed()
feed.addBarsFromCSV("trades-mgtox-usd-2013-01.csv")

# Run the strategy with the feed's bars.
myStrategy = MyStrategy(feed)
myStrategy.run()

