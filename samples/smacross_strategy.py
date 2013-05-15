from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

class Strategy(strategy.Strategy):
	def __init__(self, feed, instrument, smaPeriod, cash=1000):
		strategy.Strategy.__init__(self, feed, cash)
		self.__close = feed[instrument].getCloseDataSeries()
		self.__sma = ma.SMA(self.__close, smaPeriod)
		self.__instrument = instrument
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
		# If a position was not opened, check if we should enter a long position.
		if self.__position == None:
			if cross.cross_above(self.__close, self.__sma) > 0:
				# Enter a buy market order for 10 shares. The order is good till canceled.
				self.__position = self.enterLong(self.__instrument, 10, True)
		# Check if we have to exit the position.
		elif cross.cross_below(self.__close, self.__sma) > 0:
			 self.exitPosition(self.__position)

