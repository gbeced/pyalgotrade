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

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

class Series:
	def __init__(self):
		self.__values = {} # date -> value

	def addValue(self, dateTime, value):
		self.__values[dateTime] = value

	def getValue(self, dateTime):
		return self.__values.get(dateTime, None)

class Subplot:
	def __init__(self):
		self.__series = {}

	def getSeries(self, name):
		try:
			ret = self.__series[name]
		except KeyError:
			ret = Series()
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
			mplSubplot.plot(dateTimes, values)

		# Legend
		mplSubplot.legend(self.__series.keys(), shadow=True, loc="best")
		self.customizeSubplot(mplSubplot)

class StrategyPlotter:
	def __init__(self, strat):
		self.__strategy = strat
		self.__dateTimes = set()
		self.__mainSubplot = Subplot()
		self.__portfolioSubplot = Subplot()
		self.__subplots = [self.__mainSubplot, self.__portfolioSubplot]

		# This is to feed
		# - The main subplot with bar values.
		# - The portfolio evolution subplot.
		strat.getBarsProcessedEvent().subscribe(self.__onBarsProcessed)

	def __onBarsProcessed(self, strat, bars):
		dateTime = bars.getDateTime()
		self.__dateTimes.add(dateTime)

		# Feed the main subplot with bar values.
		for instrument in bars.getInstruments():
			self.__mainSubplot.getSeries(instrument).addValue(dateTime, bars.getBar(instrument).getClose())

		# Feed the portfolio evolution subplot.
		self.__portfolioSubplot.getSeries("Portfolio").addValue(dateTime, self.__strategy.getBroker().getValue(bars))

	def getMainSubPlot(self):
		return self.__mainSubplot

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

