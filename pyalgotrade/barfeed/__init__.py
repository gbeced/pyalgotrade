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
from pyalgotrade import warninghelpers

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
		self.__currentBars = None
		self.__lastBars = {}
		self.__frequency = frequency

	def __getNextBarsAndUpdateDS(self):
		bars = self.getNextBars()
		if bars != None:
			self.__currentBars = bars
			# Update self.__lastBars and the dataseries.
			for instrument in bars.getInstruments():
				bar_ = bars.getBar(instrument)
				self.__lastBars[instrument] = bar_ 
				self.__ds[instrument].appendValue(bar_)
		return bars

	def __iter__(self):
		return self

	def next(self):
		if self.stopDispatching():
			raise StopIteration()
		return self.__getNextBarsAndUpdateDS()

	def getFrequency(self):
		return self.__frequency

	def getCurrentBars(self):
		"""Returns the current :class:`pyalgotrade.bar.Bars`."""
		return self.__currentBars

	def getLastBars(self):
		warninghelpers.deprecation_warning("getLastBars will be deprecated in the next version. Please use getCurrentBars instead.", stacklevel=2)
		return self.getCurrentBars()

	def getLastBar(self, instrument):
		"""Returns the last :class:`pyalgotrade.bar.Bar` for a given instrument, or None."""
		return self.__lastBars.get(instrument, None)

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
		bars = self.__getNextBarsAndUpdateDS()
		if bars != None:
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

	def __getitem__(self, instrument):
		"""Returns the :class:`pyalgotrade.dataseries.BarDataSeries` for a given instrument.
		If the instrument is not found an exception is raised."""
		return self.__ds[instrument]

	def __contains__(self, instrument):
		"""Returns True if a :class:`pyalgotrade.dataseries.BarDataSeries` for the given instrument is available."""
		return instrument in self.__ds

# This class is responsible for:
# - Checking the pyalgotrade.bar.Bar objects returned by fetchNextBars and building pyalgotrade.bar.Bars objects.
#
# Subclasses should implement:
# - fetchNextBars

class BarFeed(BasicBarFeed):
	"""Base class for :class:`pyalgotrade.bar.Bars` providing feeds.

	:param frequency: The bars frequency.
	:type frequency: barfeed.Frequency.MINUTE or barfeed.Frequency.DAY.

	.. note::
		This is a base class and should not be used directly.
	"""
	def __init__(self, frequency):
		BasicBarFeed.__init__(self, frequency)
		self.__prevDateTime = None

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


