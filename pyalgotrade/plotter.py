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

class Subplot:
	def __init__(self):
		self.__values = {} # date -> signals -> value
		self.__signalNames = set()

	def getSignalValue(self, signalName, dateTime):
		ret = None
		signals = self.__values.get(dateTime, None)
		if signals != None:
			ret = signals.get(signalName, None)
		return ret

	def addSignalValue(self, signalName, dateTime, value):
		self.__signalNames.add(signalName)
		self.__values.setdefault(dateTime, {})
		self.__values[dateTime][signalName] = value

	def plot(self, mplSubplot, dateTimes):
		for signalName in self.__signalNames:
			values = []
			for dateTime in dateTimes:
				values.append(self.getSignalValue(signalName, dateTime))
			mplSubplot.plot(dateTimes, values)

class StrategyPlotter:
	def __init__(self, strat):
		self.__strategy = strat
		strat.getFeed().getNewBarsEvent().subscribe(self.__onBars)
		self.__dateTimes = set()
		self.__subplots = [Subplot()]

	def __onBars(self, bars):
		dateTime = bars.getDateTime()
		self.__dateTimes.add(dateTime)
		for instrument in bars.getInstruments():
			self.__subplots[0].addSignalValue(instrument, dateTime, bars.getBar(instrument).getClose())

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

