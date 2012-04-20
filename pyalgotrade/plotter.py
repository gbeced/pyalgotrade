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

class Subplot:
	colors = ['b', 'c', 'm', 'y', 'k']

	def __init__(self):
		self.__series = {}
		self.__ds = {}
		self.__nextColor = 1

	def __getColor(self, series):
		ret = series.getColor()
		if ret == None:
			ret = Subplot.colors[len(Subplot.colors) % self.__nextColor]
			self.__nextColor += 1
		return ret

	def addDataSeries(self, name, ds):
		self.__ds[ds] = self.getSeries(name)

	def addValuesFromDataSeries(self, dateTime):
		for ds, series in self.__ds.iteritems():
			series.addValue(dateTime, ds.getValue())

	def getSeries(self, name, defaultClass=Series):
		try:
			ret = self.__series[name]
		except KeyError:
			ret = defaultClass()
			self.__series[name] = ret
		return ret

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
	def __init__(self, strat, plotAllClosingPrices=True, plotBuySell=True, plotPortfolio=True):
		self.__dateTimes = set()
		self.__subplots = []
		self.__plotAllClosingPrices = plotAllClosingPrices

		self.__mainSubplot = Subplot()
		self.__subplots.append(self.__mainSubplot)

		self.__portfolioSubplot = None
		if plotPortfolio:
			self.__portfolioSubplot = Subplot()
			self.__subplots.append(self.__portfolioSubplot)


		# This is to feed:
		# - The main subplot with bar values.
		# - The portfolio evolution subplot.
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
				self.__mainSubplot.getSeries(instrument).addValue(dateTime, bars.getBar(instrument).getClose())

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

	def getMainSubPlot(self):
		return self.__mainSubplot

	def getPortfolioSubPlot(self):
		return self.__portfolioSubplot

	def plot(self):
		dateTimes = [dateTime for dateTime in self.__dateTimes]
		dateTimes.sort()

		# Build each subplot.
		fig = plt.figure()
		for i in range(len(self.__subplots)):
			mplSubplot = fig.add_subplot(len(self.__subplots), 1, i+1)
			self.__subplots[i].plot(mplSubplot, dateTimes)
			mplSubplot.grid(True)

		# Display
		plt.show()

