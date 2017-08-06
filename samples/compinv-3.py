import csv
import datetime
import os

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import strategy
from pyalgotrade.utils import stats
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe


class OrdersFile:
    def __init__(self, ordersFile):
        self.__orders = {}
        self.__firstDate = None
        self.__lastDate = None
        self.__instruments = []

        # Load orders from the file.
        reader = csv.DictReader(open(ordersFile, "r"), fieldnames=["year", "month", "day", "symbol", "action", "qty"])
        for row in reader:
            dateTime = datetime.datetime(int(row["year"]), int(row["month"]), int(row["day"]))
            self.__orders.setdefault(dateTime, [])
            order = (row["symbol"], row["action"], int(row["qty"]))
            self.__orders[dateTime].append(order)

            # As we process the file, store instruments, first date, and last date.
            if row["symbol"] not in self.__instruments:
                self.__instruments.append(row["symbol"])

            if self.__firstDate is None:
                self.__firstDate = dateTime
            else:
                self.__firstDate = min(self.__firstDate, dateTime)

            if self.__lastDate is None:
                self.__lastDate = dateTime
            else:
                self.__lastDate = max(self.__lastDate, dateTime)

    def getFirstDate(self):
        return self.__firstDate

    def getLastDate(self):
        return self.__lastDate

    def getInstruments(self):
        return self.__instruments

    def getOrders(self, dateTime):
        return self.__orders.get(dateTime, [])


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, cash, ordersFile, useAdjustedClose):
        # Suscribe to the feed bars event before the broker just to place the orders properly.
        feed.getNewValuesEvent().subscribe(self.__onBarsBeforeBroker)
        super(MyStrategy, self).__init__(feed, cash)
        self.__ordersFile = ordersFile
        self.setUseAdjustedValues(useAdjustedClose)
        # We will allow buying more shares than cash allows.
        self.getBroker().setAllowNegativeCash(True)

    def __onBarsBeforeBroker(self, dateTime, bars):
        for instrument, action, quantity in self.__ordersFile.getOrders(dateTime):
            if action.lower() == "buy":
                self.marketOrder(instrument, quantity, onClose=True)
            else:
                self.marketOrder(instrument, quantity*-1, onClose=True)

    def onOrderUpdated(self, order):
        if order.isCanceled():
            raise Exception("Order canceled. Ran out of cash ?")

    def onBars(self, bars):
        portfolioValue = self.getBroker().getEquity()
        self.info("Portfolio value: $%.2f" % (portfolioValue))


def main():
    # Load the orders file.
    ordersFile = OrdersFile("orders.csv")
    print("First date", ordersFile.getFirstDate())
    print("Last date", ordersFile.getLastDate())
    print("Symbols", ordersFile.getInstruments())

    # Load the data from QSTK storage. QS environment variable has to be defined.
    if os.getenv("QS") is None:
        raise Exception("QS environment variable not defined")
    feed = yahoofeed.Feed()
    feed.setBarFilter(csvfeed.DateRangeFilter(ordersFile.getFirstDate(), ordersFile.getLastDate()))
    feed.setDailyBarTime(datetime.time(0, 0, 0))  # This is to match the dates loaded with the ones in the orders file.
    for symbol in ordersFile.getInstruments():
        feed.addBarsFromCSV(symbol, os.path.join(os.getenv("QS"), "QSData", "Yahoo", symbol + ".csv"))

    # Run the strategy.
    cash = 1000000
    useAdjustedClose = True
    myStrategy = MyStrategy(feed, cash, ordersFile, useAdjustedClose)

    # Attach returns and sharpe ratio analyzers.
    retAnalyzer = returns.Returns()
    myStrategy.attachAnalyzer(retAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    myStrategy.attachAnalyzer(sharpeRatioAnalyzer)

    myStrategy.run()

    # Print the results.
    print("Final portfolio value: $%.2f" % myStrategy.getResult())
    print("Anual return: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100))
    print("Average daily return: %.2f %%" % (stats.mean(retAnalyzer.getReturns()) * 100))
    print("Std. dev. daily return: %.4f" % (stats.stddev(retAnalyzer.getReturns())))
    print("Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0)))

main()
