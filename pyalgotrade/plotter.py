# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import broker

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def _min(value1, value2):
	if value1 is None:
		return value2
	elif value2 is None:
		return value1
	else:
		return min(value1, value2)

def _max(value1, value2):
	if value1 is None:
		return value2
	elif value2 is None:
		return value1
	else:
		return max(value1, value2)

def _adjustXAxis(mplSubplots):
	minX = None
	maxX = None

	# Calculate min and max x values.
	for mplSubplot in mplSubplots:
		axis = mplSubplot.axis()
		minX = _min(minX, axis[0])
		maxX = _max(maxX, axis[1])

	for mplSubplot in mplSubplots:
		axis = mplSubplot.axis()
		axis = (minX, maxX, axis[2], axis[3])
		mplSubplot.axis(axis)

def _filter_datetimes(dateTimes, fromDate = None, toDate = None):
	class DateTimeFilter:
		def __init__(self, fromDate = None, toDate = None):
			self.__fromDate = fromDate
			self.__toDate = toDate

		def includeDateTime(self, dateTime):
			if self.__toDate and dateTime > self.__toDate:
				return False
			if self.__fromDate and dateTime < self.__fromDate:
				return False
			return True

	dateTimeFilter = DateTimeFilter(fromDate, toDate)
	return filter(lambda x: dateTimeFilter.includeDateTime(x), dateTimes)

class Series:
	def __init__(self):
		self.__values = {}

	def getColor(self):
		return None

	def getMarker(self):
		return "-"

	def addValue(self, dateTime, value):
		self.__values[dateTime] = value

	def getValue(self, dateTime):
		return self.__values.get(dateTime, None)

class BuyMarker(Series):
	def getColor(self):
		return 'g'

	def getMarker(self):
		return "^"

class SellMarker(Series):
	def getColor(self):
		return 'r'

	def getMarker(self):
		return "v"

class CustomMarker(Series):
	def getMarker(self):
		return "o"

class Subplot:
	""" """
	colors = ['b', 'c', 'm', 'y', 'k']

	def __init__(self):
		self.__series = {}
		self.__dataSeries = {}
		self.__nextColor = 1

	def __getColor(self, series):
		ret = series.getColor()
		if ret == None:
			ret = Subplot.colors[len(Subplot.colors) % self.__nextColor]
			self.__nextColor += 1
		return ret

	def addDataSeries(self, label, dataSeries):
		"""Adds a DataSeries to the subplot.

		:param label: A name for the DataSeries values.
		:type label: string.
		:param dataSeries: The DataSeries to add.
		:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
		"""
		self.__dataSeries[dataSeries] = self.getSeries(label)

	def addValuesFromDataSeries(self, dateTime):
		for ds, series in self.__dataSeries.iteritems():
			series.addValue(dateTime, ds.getValue())

	def getSeries(self, name, defaultClass=Series):
		try:
			ret = self.__series[name]
		except KeyError:
			ret = defaultClass()
			self.__series[name] = ret
		return ret

	def getCustomMarksSeries(self, name):
		return self.getSeries(name, CustomMarker)

	def customizeSubplot(self, mplSubplot):
		# Don't scale the Y axis
		mplSubplot.yaxis.set_major_formatter(ticker.ScalarFormatter(useOffset=False))

	def plot(self, mplSubplot, dateTimes):
		for seriesName in self.__series.keys():
			series = self.getSeries(seriesName)
			values = []
			for dateTime in dateTimes:
				values.append(series.getValue(dateTime))
			mplSubplot.plot(dateTimes, values, color=self.__getColor(series), marker=series.getMarker())

		# Legend
		mplSubplot.legend(self.__series.keys(), shadow=True, loc="best")
		self.customizeSubplot(mplSubplot)

class StrategyPlotter:
	"""Class responsible for plotting a strategy execution.

	:param strat: The strategy to plot.
	:type strat: :class:`pyalgotrade.strategy.Strategy`.
	:param plotAllClosingPrices: Set to True to get the closing prices plotted.
	:type plotAllClosingPrices: boolean.
	:param plotBuySell: Set to True to get the buy/sell events plotted.
	:type plotBuySell: boolean.
	:param plotPortfolio: Set to True to get the portfolio value (shares + cash) plotted.
	:type plotPortfolio: boolean.
	"""

	def __init__(self, strat, plotAllClosingPrices=True, plotBuySell=True, plotPortfolio=True):
		self.__dateTimes = set()
		self.__subplots = []
		self.__namedSubplots = {}
		self.__plotAllClosingPrices = plotAllClosingPrices
		self.__plotAdjClose = False

		self.__mainSubplot = Subplot()
		self.__subplots.append(self.__mainSubplot)

		self.__portfolioSubplot = None
		if plotPortfolio:
			self.__portfolioSubplot = Subplot()
			self.__subplots.append(self.__portfolioSubplot)

		# This is to feed:
		# - Record datetimes
		# - Feed the main subplot with bar values.
		# - Feed the portfolio evolution subplot.
		strat.getBarsProcessedEvent().subscribe(self.__onBarsProcessed)

		# This is to feed buy/sell markes in the main subplot.
		if plotBuySell:
			strat.getBroker().getOrderUpdatedEvent().subscribe(self.__onOrderUpdated)

	def __onBarsProcessed(self, strat, bars):
		dateTime = bars.getDateTime()
		self.__dateTimes.add(dateTime)

		for subplot in self.__subplots:
			subplot.addValuesFromDataSeries(dateTime)

		# Feed the main subplot with bar values.
		if self.__plotAllClosingPrices:
			for instrument in bars.getInstruments():
				if self.__plotAdjClose:
					price = bars.getBar(instrument).getAdjClose()
				else:
					price = bars.getBar(instrument).getClose()
				self.__mainSubplot.getSeries(instrument).addValue(dateTime, price)

		# Feed the portfolio evolution subplot.
		if self.__portfolioSubplot:
			self.__portfolioSubplot.getSeries("Portfolio").addValue(dateTime, strat.getBroker().getValue(bars))

	def __onOrderUpdated(self, broker_, order):
		if order.isFilled():
			action = order.getAction()
			execInfo = order.getExecutionInfo()
			if action == broker.Order.Action.BUY:
				self.__mainSubplot.getSeries("Buy", BuyMarker).addValue(execInfo.getDateTime(), execInfo.getPrice())
			elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
				self.__mainSubplot.getSeries("Sell", SellMarker).addValue(execInfo.getDateTime(), execInfo.getPrice())

	def setPlotAdjClose(self, plotAdjClose):
		self.__plotAdjClose = plotAdjClose

	def getMainSubplot(self):
		"""Returns the main subplot, where closing prices and buy/sell events get plotted.

		:rtype: :class:`Subplot`.
		"""
		return self.__mainSubplot

	def getPortfolioSubplot(self):
		"""Returns the subplot where the portfolio values get plotted.

		:rtype: :class:`Subplot`.
		"""
		return self.__portfolioSubplot

	def getOrCreateSubplot(self, name):
		"""Returns a Subplot by name. If the subplot doesn't exist, it gets created.

		:param name: The name of the Subplot to get or create.
		:type name: string.
		:rtype: :class:`Subplot`.
		"""
		try:
			ret = self.__namedSubplots[name]
		except KeyError:
			ret = Subplot()
			self.__namedSubplots[name] = ret
			self.__subplots.append(ret)
		return ret

	def plot(self, fromDateTime = None, toDateTime = None):
		"""Plots the strategy execution. Must be called after running the strategy.

		:param fromDateTime: An optional starting datetime.datetime. Everyting before it won't get plotted.
		:type fromDateTime: datetime.datetime
		:param toDateTime: An optional ending datetime.datetime. Everyting after it won't get plotted.
		:type toDateTime: datetime.datetime
		"""

		# dateTimes = [dateTime for dateTime in self.__dateTimes]
		dateTimes = _filter_datetimes(self.__dateTimes, fromDateTime, toDateTime)
		dateTimes.sort()

		# Build each subplot.
		fig = plt.figure()
		mplSubplots = []
		for i in range(len(self.__subplots)):
			mplSubplot = fig.add_subplot(len(self.__subplots), 1, i+1)
			mplSubplots.append(mplSubplot)
			self.__subplots[i].plot(mplSubplot, dateTimes)
			mplSubplot.grid(True)

		_adjustXAxis(mplSubplots)

		# Display
		plt.show()

