from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.tools import yahoofinance
from pyalgotrade.technical import vwap


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, vwapWindowSize):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__vwap = vwap.VWAP(feed[instrument], vwapWindowSize)

    def getVWAPDS(self):
        return self.__vwap

    def onBars(self, bars):
        vwap = self.__vwap[-1]
        if vwap is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        price = bars[self.__instrument].getClose()
        notional = shares * price
        if price < vwap * 0.995 and notional > 0:
            self.order(self.__instrument, -100)
        elif price > vwap * 1.005 and notional < 1000000:
            self.order(self.__instrument, 100)


def main(plot):
    instrument = "aapl"
    vwapWindowSize = 5

    # Download the bars.
    feed = yahoofinance.build_feed([instrument], 2011, 2012, ".")

    myStrategy = MyStrategy(feed, instrument, vwapWindowSize)

    if plot:
        plt = plotter.StrategyPlotter(myStrategy, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("vwap", myStrategy.getVWAPDS())

    myStrategy.run()
    print "Result: %.2f" % myStrategy.getResult()

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
