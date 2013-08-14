from pyalgotrade import plotter
from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import broker

import mtgox_scalper

def main(plot):
    # Load the trades from the CSV file
    print "Loading bars"
    feed = barfeed.CSVTradeFeed()
    feed.addBarsFromCSV("trades-mtgox-usd-2013-03.csv")

    # Create a backtesting broker.
    brk = broker.BacktestingBroker(200, feed)

    # Run the strategy with the feed and the broker.
    print "Running strategy"
    strat = mtgox_scalper.Strategy("BTC", feed, brk)

    if plot:
        plt = plotter.StrategyPlotter(strat, plotBuySell=False)
        plt.getOrCreateSubplot("volatility").addDataSeries("Volatility", strat.returnsVolatility)

    strat.run()
    print "Result: %.2f" % strat.getResult()

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
