from __future__ import print_function

import sma_crossover
from pyalgotrade.tools import quandl
from pyalgotrade.stratanalyzer import sharpe


def main(plot):
    symbol = "AAPL"
    priceCurrency = "USD"
    instrument = "%s/%s" % (symbol, priceCurrency)
    smaPeriod = 163

    # Download the bars.
    feed = quandl.build_feed("WIKI", [symbol], priceCurrency, 2011, 2012, ".")

    strat = sma_crossover.SMACrossOver(feed, instrument, smaPeriod)
    sharpeRatioAnalyzer = sharpe.SharpeRatio(priceCurrency)
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        from pyalgotrade import plotter

        plt = plotter.StrategyPlotter(strat, True, False, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("sma", strat.getSMA())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
