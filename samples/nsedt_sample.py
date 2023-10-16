import nsedt

import pyalgotrade.utils.Utils
from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.barfeed import nsedtfeed
from pyalgotrade.tools import quandl, NseDT
from pyalgotrade.feed import csvfeed
from datetime import date, datetime

import pyalgotrade.tools.NseDT
from pyalgotrade.utils import Utils
from pyalgotrade.utils.Utils import get_data_file_path


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, nsedtFeed, instrument):
        super(MyStrategy, self).__init__(feed)
        self.__instrument = instrument

        # It is VERY important to add the the extra feed to the event dispatch loop before
        # running the strategy.
        self.getDispatcher().addSubject(nsedtFeed)

        # Subscribe to events from the Nsedt feed.
        nsedtFeed.getNewValuesEvent().subscribe(self.onNsedtData)

    def onNsedtData(self, dateTime, values):
        self.info(values)

    def onBars(self, bars):
        self.info(bars[self.__instrument].getAdjClose())


def main(plot):
    instruments = ["DIXON"]

    # Download GORO bars using WIKI source code.
    startdate = date(year=2001, month=1, day=1)
    enddate = date(year=2022, month=1, day=1)
    feed = NseDT.build_feed(instruments, startdate=startdate, enddate=enddate)

    # Load Quandl CSV downloaded from http://www.quandl.com/OFDP-Open-Financial-Data-Project/GOLD_2-LBMA-Gold-Price-London-Fixings-P-M
    nsedtFeed = csvfeed.Feed("Date", "%Y-%m-%d")
    # nsedtFeed.setDateRange(datetime(2006, 1, 1), datetime(2012, 12, 31))
    filepath = get_data_file_path(pyalgotrade.utils.Utils.getNSEFileName("DIXON", startdate, enddate) + '.csv')
    print(filepath)
    nsedtFeed.addValuesFromCSV(filepath)

    myStrategy = MyStrategy(feed, nsedtFeed, instruments[0])

    if plot:
        plt = plotter.StrategyPlotter(myStrategy, True, True, True)
        plt.getOrCreateSubplot("nse").addDataSeries("Open", feed.getColumnName("open"))
        plt.getOrCreateSubplot("nse").addDataSeries("Close", feed.getColumnName("close"))

    myStrategy.run()

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
