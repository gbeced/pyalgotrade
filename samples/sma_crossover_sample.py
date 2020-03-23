from __future__ import print_function

import sma_crossover
from pyalgotrade.tools import quandl
from pyalgotrade.stratanalyzer import sharpe


def main(plot):
    instrument = "AAPL"
    priceCurrency = "USD"
    smaPeriod = 163

    # Download the bars.
    feed = quandl.build_feed("WIKI", [instrument], priceCurrency, 2011, 2012, ".")

    strat = sma_crossover.SMACrossOver(feed, instrument, priceCurrency, smaPeriod)
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
