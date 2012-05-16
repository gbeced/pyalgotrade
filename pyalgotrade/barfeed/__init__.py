# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import dataseries
from pyalgotrade import observer
from pyalgotrade import bar
import session

class BasicBarFeed:
	def __init__(self):
		self.__ds = {}
		self.__defaultInstrument = None
		self.__newBarsEvent = observer.Event()

	def getNewBarsEvent(self):
		return self.__newBarsEvent

	def getDefaultInstrument(self):
		"""Returns the default instrument."""
		return self.__defaultInstrument

	# Process every element in the feed and emit an event for each one.
	def processAll(self):
		for bars in self:
			self.__newBarsEvent.emit(bars)

	def getRegisteredInstruments(self):
		"""Returns a list of registered intstrument names."""
		return self.__ds.keys()

	def registerInstrument(self, instrument):
		if self.__defaultInstrument != None and instrument != self.__defaultInstrument:
			raise Exception("Multiple instruments not supported")

		self.__defaultInstrument = instrument
		if instrument not in self.__ds:
			self.__ds[instrument] = dataseries.BarDataSeries()

	def getDataSeries(self, instrument = None):
		"""Returns the :class:`pyalgotrade.dataseries.BarDataSeries` for a given instrument.

		:param instrument: Instrument identifier. If None, the default instrument is returned.
		:type instrument: string.
		:rtype: :class:`pyalgotrade.dataseries.BarDataSeries`.
		"""
		assert(instrument == None or instrument == self.__defaultInstrument)
		return self.__ds[self.__defaultInstrument]

class BarFeed(BasicBarFeed):
	"""Base class for :class:`pyalgotrade.bar.Bar` providing feeds.

	.. note::
		This is a base class and should not be used directly.
	"""
	def __init__(self):
		BasicBarFeed.__init__(self)
		self.__sessionCloseStrategy = session.DaySessionCloseStrategy()
		self.__prevDateTime = None
		self.__barBuff = []

	# Override to return a map from instrument names to bars or None if there is no more data. All bars datetime must be equal.
	def fetchNextBars(self):
		raise Exception("Not implemented")

	def __loadBars(self):
		while len(self.__barBuff) < 2:
			barDict = self.fetchNextBars()
			self.__barBuff.append(barDict)

	def __iter__(self):
		return self

	def next(self):
		"""Returns the next :class:`pyalgotrade.bar.Bars` in the feed. If there are not more values StopIteration is raised."""
		self.__loadBars()
		if self.__barBuff[0] == None:
			raise StopIteration()

		barDict = self.__barBuff.pop(0)
		nextBarDict = self.__barBuff[0] # nextBarDict may be None

		# Check that bars were retured for all the instruments registered.
		if barDict.keys() != self.getRegisteredInstruments():
			raise Exception("Some bars are missing")

		currentDateTime = None
		firstBarInstrument = None
		for instrument, currentBar in barDict.iteritems():
			if currentDateTime is None:
				firstBarInstrument = instrument
				currentDateTime = currentBar.getDateTime()
			# Check that current bar datetimes are in sync
			elif currentBar.getDateTime() != currentDateTime:
				raise Exception("Bar data times are not in sync. %s %s != %s %s" % (instrument, currentBar.getDateTime(), firstBarInstrument, currentDateTime))

			# Set session close
			nextBar = None
			if nextBarDict != None:
				try:
					nextBar = nextBarDict[instrument]
				except KeyError:
					pass
			sessionClose = self.__sessionCloseStrategy.sessionClose(currentBar, nextBar)
			currentBar.setSessionClose(sessionClose)

			# Add the bar to the data source.
			self.getDataSeries(instrument).appendValue(currentBar)

		# Check that current bar datetimes are greater than the previous one.
		if self.__prevDateTime != None and self.__prevDateTime >= currentDateTime:
			raise Exception("Bar data times are not in order")
		self.__prevDateTime = currentDateTime

		return bar.Bars(barDict, currentDateTime)

# This class is used by the optimizer module. The barfeed is already built on the server side, and the bars are sent back to workers.
class OptimizerBarFeed(BasicBarFeed):
	def __init__(self, instruments, bars):
		BasicBarFeed.__init__(self)
		for instrument in instruments:
			self.registerInstrument(instrument)
		self.__bars = bars
		self.__currentBar = 0

	def __iter__(self):
		return self

	def next(self):
		if self.__currentBar >= len(self.__bars):
			raise StopIteration()

		bars = self.__bars[self.__currentBar]
		self.__currentBar += 1

		# Fill in the dataseries.
		for instrument in bars.getInstruments():
			self.getDataSeries(instrument).appendValue(bars.getBar(instrument))

		return bars

