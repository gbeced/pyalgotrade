from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown

class MyStrategy(strategy.Strategy):
	def __init__(self, feed, smaPeriod):
		strategy.Strategy.__init__(self, feed, 1000)
		closeDS = feed.getDataSeries("orcl").getCloseDataSeries()
		self.__sma = ma.SMA(closeDS, smaPeriod)
		self.__crossAbove = cross.CrossAbove(closeDS, self.__sma)
		self.__crossBelow = cross.CrossBelow(closeDS, self.__sma)
		self.__position = None

	def getSMA(self):
		return self.__sma

	def onEnterCanceled(self, position):
		self.__position = None

	def onExitOk(self, position):
		self.__position = None

	def onExitCanceled(self, position):
		# If the exit was canceled, re-submit it.
		self.exitPosition(self.__position)

	def onBars(self, bars):
		# Wait for enough bars to be available to calculate the CrossAbove indicator.
		if self.__crossAbove is None:
			return

		# If a position was not opened, check if we should enter a long position.
		if self.__position == None:
			if self.__crossAbove.getValue() > 0:
				# Enter a buy market order for 10 orcl shares. The order is good till canceled.
				self.__position = self.enterLong("orcl", 10, True)
		# Check if we have to exit the position.
		elif self.__crossBelow.getValue() > 0:
			 self.exitPosition(self.__position)

# Load the yahoo feed from the CSV file
feed = yahoofeed.Feed()
feed.addBarsFromCSV("orcl", "orcl-2000.csv")

# Evaluate the strategy with the feed's bars.
myStrategy = MyStrategy(feed, 20)

# Attach different analyzers to a strategy before executing it.
retAnalyzer = returns.ReturnsAnalyzer()
myStrategy.attachAnalyzer(retAnalyzer)
sharpeRatioAnalyzer = sharpe.SharpeRatio()
myStrategy.attachAnalyzer(sharpeRatioAnalyzer)
drawDownAnalyzer = drawdown.DrawDown()
myStrategy.attachAnalyzer(drawDownAnalyzer)

# Run the strategy.
myStrategy.run()

print "Final portfolio value: $%.2f" % myStrategy.getResult()
print "Cumulative returns: %.2f %%" % (retAnalyzer.getCumulativeReturn() * 100)
print "Sharpe ratio: %.2f" % (sharpeRatioAnalyzer.getSharpeRatio(0.05, 252))
print "Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100)
print "Max. drawdown duration: %d days" % (drawDownAnalyzer.getMaxDrawDownDuration())

