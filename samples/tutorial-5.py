from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

class MyStrategy(strategy.Strategy):
	def __init__(self, feed, smaPeriod):
		strategy.Strategy.__init__(self, feed, 1000)
		closeDS = feed.getDataSeries("orcl").getCloseDataSeries()
		self.__sma = ma.SMA(closeDS, smaPeriod)
		self.__crossAbove = cross.CrossAbove(closeDS, self.__sma)
		self.__crossBelow = cross.CrossBelow(closeDS, self.__sma)
		self.__position = None
		self.__result = 0

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

	def onFinish(self, bars):
		print "Final portfolio value: $%.2f" % self.getBroker().getValue(bars)
		self.__result = self.getBroker().getValue(bars)

	def getResult(self):
		return self.__result

def run_strategy(smaPeriod):
	# Load the yahoo feed from the CSV file
	feed = csvfeed.YahooFeed()
	feed.addBarsFromCSV("orcl", "orcl-2000.csv")

	# Evaluate the strategy with the feed's bars.
	myStrategy = MyStrategy(feed, smaPeriod)
	# Attach the strategy to the plotter.
	plt = plotter.StrategyPlotter(myStrategy)
	# Include the SMA in the main subplot, to get it displayed along with the closing prices.
	plt.getMainSubplot().addDataSeries("SMA", myStrategy.getSMA())
	# Run the strategy.
	myStrategy.run()
	# Plot the strategy.
	plt.plot()

run_strategy(20)

