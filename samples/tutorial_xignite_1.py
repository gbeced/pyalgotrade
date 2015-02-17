from pyalgotrade import strategy
from pyalgotrade.bar import Frequency
from pyalgotrade.xignite import barfeed
from pyalgotrade.broker import backtesting
from pyalgotrade.technical import ma


class Strategy(strategy.BaseStrategy):
    def __init__(self, feed, brk):
        strategy.BaseStrategy.__init__(self, feed, brk)
        self.__sma = {}
        for instrument in feed.getRegisteredInstruments():
            self.__sma[instrument] = ma.SMA(feed[instrument].getCloseDataSeries(), 5)

    def onBars(self, bars):
        for instrument in bars.getInstruments():
            bar = bars[instrument]
            self.info("%s: Open: %s High: %s Low: %s Close: %s Volume: %s SMA: %s" % (instrument, bar.getOpen(), bar.getHigh(), bar.getLow(), bar.getClose(), bar.getVolume(), self.__sma[instrument][-1]))


def main():
    # Replace apiToken with your own API token.
    apiToken = "<YOUR API TOKEN HERE>"
    # indentifiers are fully qualified identifiers for the security and must include the exchange suffix.
    indentifiers = ["RIOl.CHIX", "HSBAl.CHIX"]
    # apiCallDelay is necessary because the bar may not be immediately available.
    apiCallDelay = 60

    feed = barfeed.LiveFeed(apiToken, indentifiers, Frequency.MINUTE*5, apiCallDelay)
    brk = backtesting.Broker(1000, feed)
    myStrategy = Strategy(feed, brk)
    myStrategy.run()

if __name__ == "__main__":
    main()
