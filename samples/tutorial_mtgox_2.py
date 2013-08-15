from pyalgotrade.mtgox import client
from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import broker

import mtgox_scalper

def main():
    # Create a client responsible for all the interaction with MtGox
    cl = client.Client("USD", None, None)

    # Create a real-time feed that will build bars from live trades.
    feed = barfeed.LiveTradeFeed(cl)

    # Create a backtesting broker.
    brk = broker.BacktestingBroker(200, feed)

    # Run the strategy with the feed and the broker.
    strat = mtgox_scalper.Strategy("BTC", feed, brk)
    # It is VERY important to add the client to the event dispatch loop before running the strategy.
    strat.getDispatcher().addSubject(cl)
    # This is just to get each bar printed.
    strat.setVerbosityLevel(0)
    strat.run()

if __name__ == "__main__":
    main()
