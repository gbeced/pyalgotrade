from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import plotter
from pyalgotrade.tools import yahoofinance
from pyalgotrade.technical import bollinger

import os

class MyStrategy(strategy.Strategy):
	def __init__(self, feed, instrument, bBandsPeriod):
		strategy.Strategy.__init__(self, feed)
		self.__instrument = instrument
		self.__bbands = bollinger.BollingerBands(feed[instrument].getCloseDataSeries(), bBandsPeriod, 2)

	def getBollingerBands(self):
		return self.__bbands

	def onBars(self, bars):
		lower = self.__bbands.getLowerBand()[-1]
		upper = self.__bbands.getUpperBand()[-1]
		if lower == None:
			return

		shares = self.getBroker().getShares(self.__instrument)
		bar = bars[self.__instrument]
		if shares == 0 and bar.getClose() < lower:
			sharesToBuy = int(self.getBroker().getCash(False) / bar.getClose())
			self.order(self.__instrument, sharesToBuy) 
		elif shares > 0 and bar.getClose() > upper:
			self.order(self.__instrument, -1*shares) 

def build_feed(instruments, fromYear, toYear):
	feed = yahoofeed.Feed()

	for year in range(fromYear, toYear+1):
		for symbol in instruments:
			fileName = "%s-%d-yahoofinance.csv" % (symbol, year)
			if not os.path.exists(fileName):
				print "Downloading %s %d" % (symbol, year)
				csv = yahoofinance.get_daily_csv(symbol, year)
				f = open(fileName, "w")
				f.write(csv)
				f.close()
			feed.addBarsFromCSV(symbol, fileName)
	return feed

def main(plot):
	instrument = "yhoo"
	bBandsPeriod = 40

	# Download the bars.
	feed = build_feed([instrument], 2011, 2012)

	myStrategy = MyStrategy(feed, instrument, bBandsPeriod)

	if plot:
		plt = plotter.StrategyPlotter(myStrategy, True, True, True)
		plt.getInstrumentSubplot(instrument).addDataSeries("upper", myStrategy.getBollingerBands().getUpperBand())
		plt.getInstrumentSubplot(instrument).addDataSeries("middle", myStrategy.getBollingerBands().getMiddleBand())
		plt.getInstrumentSubplot(instrument).addDataSeries("lower", myStrategy.getBollingerBands().getLowerBand())

	myStrategy.run()
	print "Result: %.2f" % myStrategy.getResult()

	if plot:
		plt.plot()

if __name__ == "__main__":
	main(True)

