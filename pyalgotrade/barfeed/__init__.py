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
from pyalgotrade.barfeed import helpers

class Frequency:
	# SECOND	= 1
	MINUTE	= 2
	# HOUR	= 3
	DAY		= 4

# This class is responsible for:
# - Managing and upating BarDataSeries instances.
# - Event dispatching
#
# Subclasses should implement:
# - getNextBars
#
# THIS IS A VERY BASIC CLASS AND IN WON'T DO ANY VERIFICATIONS OVER THE BARS RETURNED.

class BasicBarFeed:
	def __init__(self, frequency):
		self.__ds = {}
		self.__defaultInstrument = None
		self.__newBarsEvent = observer.Event()
		self.__lastBars = None
		self.__frequency = frequency

	def getFrequency(self):
		return self.__frequency

	def getLastBars(self):
		return self.__lastBars

	def start(self):
		raise NotImplementedError()

	def stop(self):
		raise NotImplementedError()

	def join(self):
		raise NotImplementedError()

	# Return True if there are not more events to dispatch.
	def stopDispatching(self):
		raise NotImplementedError()

	# Subclasses should implement this and return a pyalgotrade.bar.Bars or None if there are no bars.
	def getNextBars(self):
		raise NotImplementedError()

	def getNewBarsEvent(self):
		return self.__newBarsEvent

	def getDefaultInstrument(self):
		"""Returns the default instrument."""
		return self.__defaultInstrument

	# Dispatch events.
	def dispatch(self):
		bars = self.getNextBars()
		if bars != None:
			self.__lastBars = bars
			# Update the dataseries.
			for instrument in bars.getInstruments():
				self.__ds[instrument].appendValue(bars.getBar(instrument))
			# Emit event.
			self.__newBarsEvent.emit(bars)

	def getRegisteredInstruments(self):
		"""Returns a list of registered intstrument names."""
		return self.__ds.keys()

	def registerInstrument(self, instrument):
		self.__defaultInstrument = instrument
		if instrument not in self.__ds:
			self.__ds[instrument] = dataseries.BarDataSeries()

	def getDataSeries(self, instrument = None):
		"""Returns the :class:`pyalgotrade.dataseries.BarDataSeries` for a given instrument.

		:param instrument: Instrument identifier. If None, the default instrument is returned.
		:type instrument: string.
		:rtype: :class:`pyalgotrade.dataseries.BarDataSeries`.
		"""
		if instrument == None:
			instrument = self.__defaultInstrument
		return self.__ds[instrument]

# This class is responsible for:
# - Checking the pyalgotrade.bar.Bar objects returned by fetchNextBars and building pyalgotrade.bar.Bars objects.
#
# Subclasses should implement:
# - fetchNextBars

class BarFeed(BasicBarFeed):
	"""Base class for :class:`pyalgotrade.bar.Bars` providing feeds.

	.. note::
		This is a base class and should not be used directly.
	"""
	def __init__(self, frequency):
		BasicBarFeed.__init__(self, frequency)
		self.__prevDateTime = None

	def __iter__(self):
		return self

	def next(self):
		if self.stopDispatching():
			raise StopIteration()
		return self.getNextBars()

	# Override to return a map from instrument names to bars or None if there is no data. All bars datetime must be equal.
	def fetchNextBars(self):
		raise NotImplementedError()

	def getNextBars(self):
		"""Returns the next :class:`pyalgotrade.bar.Bars` in the feed or None if there are no bars."""

		barDict = self.fetchNextBars()
		if barDict == None:
			return None

		# This will check for incosistent datetimes between bars.
		ret = bar.Bars(barDict)

		# Check that current bar datetimes are greater than the previous one.
		if self.__prevDateTime != None and self.__prevDateTime >= ret.getDateTime():
			raise Exception("Bar data times are not in order. Previous datetime was %s and current datetime is %s" % (self.__prevDateTime, ret.getDateTime()))
		self.__prevDateTime = ret.getDateTime()

		return ret

# This class is responsible for:
# - Holding bars in memory.
# - Aligning them with respect to time.
#
# Subclasses should:
# - Forward the call to start() if they override it.

class InMemoryBarFeed(BarFeed):
	def __init__(self, frequency):
		BarFeed.__init__(self, frequency)
		self.__bars = {}
		self.__nextBarIdx = {}

	def start(self):
		# Set session close attributes to bars.
		for instrument, bars in self.__bars.iteritems():
			helpers.set_session_close_attributes(bars)

	def stop(self):
		pass

	def join(self):
		pass

	def addBarsFromSequence(self, instrument, bars):
		self.__bars.setdefault(instrument, [])
		self.__nextBarIdx.setdefault(instrument, 0)

		# Add and sort the bars
		self.__bars[instrument].extend(bars)
		barCmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
		self.__bars[instrument].sort(barCmp)

		self.registerInstrument(instrument)

	def stopDispatching(self):
		ret = True
		# Check if there is at least one more bar to return.
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars):
				ret = False
				break
		return ret

	def fetchNextBars(self):
		# All bars must have the same datetime. We will return all the ones with the smallest datetime.
		smallestDateTime = None

		# Make a first pass to get the smallest datetime.
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars):
				if smallestDateTime == None or bars[nextIdx].getDateTime() < smallestDateTime:
					smallestDateTime = bars[nextIdx].getDateTime()

		if smallestDateTime == None:
			return None

		# Make a second pass to get all the bars that had the smallest datetime.
		ret = {}
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars) and bars[nextIdx].getDateTime() == smallestDateTime:
				ret[instrument] = bars[nextIdx]
				self.__nextBarIdx[instrument] += 1
		return ret

# This class is used by the optimizer module. The barfeed is already built on the server side, and the bars are sent back to workers.
class OptimizerBarFeed(BasicBarFeed):
	def __init__(self, frequency, instruments, bars):
		BasicBarFeed.__init__(self, frequency)
		for instrument in instruments:
			self.registerInstrument(instrument)
		self.__bars = bars
		self.__nextBar = 0

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

	def getNextBars(self):
		ret = None
		if self.__nextBar < len(self.__bars):
			ret = self.__bars[self.__nextBar]
			self.__nextBar += 1
		return ret

	def stopDispatching(self):
		return self.__nextBar >= len(self.__bars)


