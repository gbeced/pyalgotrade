from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade.tools import quandl
from pyalgotrade.technical import bollinger
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.broker import backtesting


class BBands(strategy.BacktestingStrategy):
    def __init__(self, feed, broker, instrument, bBandsPeriod):
        super(BBands, self).__init__(feed, brk=broker)
        self.__instrument = instrument
        self.__symbol, self.__priceCurrency = instrument.split("/")

        self.__bbands = bollinger.BollingerBands(
            feed.getDataSeries(instrument).getCloseDataSeries(),
            bBandsPeriod, 2
        )

    def getBollingerBands(self):
        return self.__bbands

    def onOrderUpdated(self, orderEvent):
        self.info(str(orderEvent))

    def onBars(self, bars):
        lower = self.__bbands.getLowerBand()[-1]
        upper = self.__bbands.getUpperBand()[-1]
        if lower is None:
            return

        shares = self.getBroker().getBalance(self.__symbol)
        bar = bars.getBar(self.__instrument)
        if shares == 0 and bar.getClose() < lower:
            sharesToBuy = self.getBroker().getBalance(self.__priceCurrency) // bar.getClose()
            self.info("Placing buy market order for %s shares" % sharesToBuy)
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and bar.getClose() > upper:
            self.info("Placing sell market order for %s shares" % shares)
            self.marketOrder(self.__instrument, -1*shares)


def main(plot):
    symbol = "yhoo"
    priceCurrency = "USD"
    instrument = "%s/%s" % (symbol, priceCurrency)
    bBandsPeriod = 40

    # Download the bars.
    feed = quandl.build_feed("WIKI", [symbol], priceCurrency, 2011, 2012, ".")
    broker = backtesting.Broker({priceCurrency: 1000000}, feed)

    strat = BBands(feed, broker, instrument, bBandsPeriod)
    sharpeRatioAnalyzer = sharpe.SharpeRatio(priceCurrency)
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    if plot:
        from pyalgotrade import plotter

        plt = plotter.StrategyPlotter(strat, True, True, True)
        plt.getInstrumentSubplot(instrument).addDataSeries("upper", strat.getBollingerBands().getUpperBand())
        plt.getInstrumentSubplot(instrument).addDataSeries("middle", strat.getBollingerBands().getMiddleBand())
        plt.getInstrumentSubplot(instrument).addDataSeries("lower", strat.getBollingerBands().getLowerBand())

    strat.run()
    print("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    if plot:
        plt.plot()


if __name__ == "__main__":
    main(True)
