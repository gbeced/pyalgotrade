from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.utils import stats


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed):
        super(MyStrategy, self).__init__(feed, 1000000)

        # We wan't to use adjusted close prices instead of close.
        self.setUseAdjustedValues(True)

        # Place the orders to get them processed on the first bar.
        orders = {
            "aeti": 297810,
            "egan": 81266,
            "glng": 11095,
            "simo": 17293,
        }
        for instrument, quantity in list(orders.items()):
            self.marketOrder(instrument, quantity, onClose=True, allOrNone=True)

    def onBars(self, bars):
        pass

# Load the yahoo feed from CSV files.
feed = yahoofeed.Feed()
feed.addBarsFromCSV("aeti", "aeti-2011-yahoofinance.csv")
feed.addBarsFromCSV("egan", "egan-2011-yahoofinance.csv")
feed.addBarsFromCSV("glng", "glng-2011-yahoofinance.csv")
feed.addBarsFromCSV("simo", "simo-2011-yahoofinance.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed)

# Attach returns and sharpe ratio analyzers.
retAnalyzer = returns.Returns()
myStrategy.attachAnalyzer(retAnalyzer)
sharpeRatioAnalyzer = sharpe.SharpeRatio()
myStrategy.attachAnalyzer(sharpeRatioAnalyzer)

# Run the strategy
myStrategy.run()

# Print the results.
print("Final portfolio value: $%.2f" % myStrategy.getResult())
print("Anual return: %.2f %%" % (retAnalyzer.getCumulativeReturns()[-1] * 100))
print("Average daily return: %.2f %%" % (stats.mean(retAnalyzer.getReturns()) * 100))
print("Std. dev. daily return: %.4f" % (stats.stddev(retAnalyzer.getReturns())))
print("Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0)))
