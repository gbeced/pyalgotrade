from pyalgotrade import strategy
from pyalgotrade.mtgox import client
from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import broker

class MyStrategy(strategy.BaseStrategy):
    def onBars(self, bars):
        bar = bars["BTC"]
        print "%s: %s %s" % (bar.getDateTime(), bar.getClose(), bar.getVolume())

# Create a client responsible for all the interaction with MtGox
cl = client.Client("USD", None, None)

# Create a real-time feed that will build bars from live trades.
feed = barfeed.LiveTradeFeed(cl)

# Create a backtesting broker.
brk = broker.BacktestingBroker(1000, feed)

# Run the strategy with the feed and the broker.
myStrategy = MyStrategy(feed, brk)
# It is VERY important to add the client to the event dispatch loop before running the strategy.
myStrategy.getDispatcher().addSubject(cl)
myStrategy.run()

