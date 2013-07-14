from pyalgotrade import strategy
from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import broker

class MyStrategy(strategy.BaseStrategy):
    def onBars(self, bars):
        bar = bars["BTC"]
        print "%s: %s %s" % (bar.getDateTime(), bar.getClose(), bar.getVolume())

# Load the trades from the CSV file
feed = barfeed.TradesCSVFeed()
feed.addBarsFromCSV("trades-mtgox-usd-2013-01.csv")

# Create a backtesting broker.
brk = broker.BacktestingBroker(1000, feed)

# Run the strategy with the feed and the broker.
myStrategy = MyStrategy(feed, brk)
myStrategy.run()

