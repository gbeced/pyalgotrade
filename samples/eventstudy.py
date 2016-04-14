from pyalgotrade import eventprofiler
from pyalgotrade.technical import stats
from pyalgotrade.technical import roc
from pyalgotrade.technical import ma
from pyalgotrade.tools import yahoofinance

# Event inspired on an example from Ernie Chan's book:
# 'Algorithmic Trading: Winning Strategies and Their Rationale'


class BuyOnGap(eventprofiler.Predicate):
    def __init__(self, feed):
        super(BuyOnGap, self).__init__()

        stdDevPeriod = 90
        smaPeriod = 20
        self.__returns = {}
        self.__stdDev = {}
        self.__ma = {}
        for instrument in feed.getRegisteredInstruments():
            priceDS = feed[instrument].getAdjCloseDataSeries()
            # Returns over the adjusted close values.
            self.__returns[instrument] = roc.RateOfChange(priceDS, 1)
            # StdDev over those returns.
            self.__stdDev[instrument] = stats.StdDev(self.__returns[instrument], stdDevPeriod)
            # MA over the adjusted close values.
            self.__ma[instrument] = ma.SMA(priceDS, smaPeriod)

    def __gappedDown(self, instrument, bards):
        ret = False
        if self.__stdDev[instrument][-1] is not None:
            prevBar = bards[-2]
            currBar = bards[-1]
            low2OpenRet = (currBar.getOpen(True) - prevBar.getLow(True)) / float(prevBar.getLow(True))
            if low2OpenRet < (self.__returns[instrument][-1] - self.__stdDev[instrument][-1]):
                ret = True
        return ret

    def __aboveSMA(self, instrument, bards):
        ret = False
        if self.__ma[instrument][-1] is not None and bards[-1].getOpen(True) > self.__ma[instrument][-1]:
            ret = True
        return ret

    def eventOccurred(self, instrument, bards):
        ret = False
        if self.__gappedDown(instrument, bards) and self.__aboveSMA(instrument, bards):
            ret = True
        return ret


def main(plot):
    instruments = ["AA", "AES", "AIG"]
    feed = yahoofinance.build_feed(instruments, 2008, 2009, ".")

    predicate = BuyOnGap(feed)
    eventProfiler = eventprofiler.Profiler(predicate, 5, 5)
    eventProfiler.run(feed, True)

    results = eventProfiler.getResults()
    print "%d events found" % (results.getEventCount())
    if plot:
        eventprofiler.plot(results)

if __name__ == "__main__":
    main(True)
