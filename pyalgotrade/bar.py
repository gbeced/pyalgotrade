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

class Bar(object):
	"""A Bar is a summary of the trading activity for a security in a given period.

	.. note::
		This is a base class and should not be used directly.
	"""

	def getDateTime(self):
		"""Returns the :class:`datetime.datetime`."""
		raise NotImplementedError()

	def getOpen(self):
		"""Returns the opening price."""
		raise NotImplementedError()

	def getHigh(self):
		"""Returns the highest price."""
		raise NotImplementedError()

	def getLow(self):
		"""Returns the lowest price."""
		raise NotImplementedError()

	def getClose(self):
		"""Returns the closing price."""
		raise NotImplementedError()

	def getVolume(self):
		"""Returns the volume."""
		raise NotImplementedError()

	def getAdjClose(self):
		"""Returns the adjusted closing price."""
		raise NotImplementedError()

	def getTypicalPrice(self):
		"""Returns the typical price."""
		return (self.getHigh() + self.getLow() + self.getClose()) / 3.0

	def getSessionClose(self):
		# Returns True if this is the last bar for the session, or False otherwise.
		raise NotImplementedError()

	def setSessionClose(self, sessionClose):
		raise NotImplementedError()

	def getBarsTillSessionClose(self):
		raise NotImplementedError()

	def setBarsTillSessionClose(self, barsTillSessionClose):
		raise NotImplementedError()

class BasicBar(Bar):
	# Optimization to reduce memory footprint.
	__slots__ = ('__dateTime', '__open', '__close', '__high', '__low', '__volume', '__adjClose', '__sessionClose', '__barsTillSessionClose')

	def __init__(self, dateTime, open_, high, low, close, volume, adjClose):
		assert(high >= open_)
		assert(high >= low)
		assert(high >= close)
		assert(low <= open_)
		assert(low <= high)
		assert(low <= close)

		self.__dateTime = dateTime
		self.__open = open_
		self.__close = close
		self.__high = high
		self.__low = low
		self.__volume = volume
		self.__adjClose = adjClose
		self.__sessionClose = False
		self.__barsTillSessionClose = None

	def __setstate__(self, state):
		(self.__dateTime, self.__open, self.__close, self.__high, self.__low, self.__volume, self.__adjClose, self.__sessionClose, self.__barsTillSessionClose) = state

	def __getstate__(self):
		return (self.__dateTime, self.__open, self.__close, self.__high, self.__low, self.__volume, self.__adjClose, self.__sessionClose, self.__barsTillSessionClose)

	def getDateTime(self):
		return self.__dateTime

	def getOpen(self):
		return self.__open

	def getHigh(self):
		return self.__high

	def getLow(self):
		return self.__low

	def getClose(self):
		return self.__close

	def getVolume(self):
		return self.__volume

	def getAdjOpen(self):
		return self.__adjClose * self.__open / float(self.__close)

	def getAdjHigh(self):
		return self.__adjClose * self.__high / float(self.__close)

	def getAdjLow(self):
		return self.__adjClose * self.__low / float(self.__close)

	def getAdjClose(self):
		return self.__adjClose

	def getSessionClose(self):
		# Returns True if this is the last bar for the session, or False otherwise.
		return self.__sessionClose

	def setSessionClose(self, sessionClose):
		self.__sessionClose = sessionClose
		if sessionClose:
			self.__barsTillSessionClose = 0

	def getBarsTillSessionClose(self):
		return self.__barsTillSessionClose

	def setBarsTillSessionClose(self, barsTillSessionClose):
		self.__barsTillSessionClose = barsTillSessionClose

class Bars:
	"""A group of :class:`Bar` objects.

	:param barDict: A map of instrument to :class:`Bar` objects.
	:type barDict: map.

	.. note::
		All bars must have the same datetime.
	"""
	def __init__(self, barDict):
		if len(barDict) == 0:
			raise Exception("No bars supplied")

		# Check that bar datetimes are in sync
		firstDateTime = None
		firstInstrument = None
		for instrument, currentBar in barDict.iteritems():
			if firstDateTime is None:
				firstDateTime = currentBar.getDateTime()
				firstInstrument = instrument
			elif currentBar.getDateTime() != firstDateTime:
				raise Exception("Bar data times are not in sync. %s %s != %s %s" % (instrument, currentBar.getDateTime(), firstInstrument, firstDateTime))

		self.__barDict = barDict
		self.__dateTime = firstDateTime

	def __getitem__(self, instrument):
		"""Returns the :class:`pyalgotrade.bar.Bar` for the given instrument. If the instrument is not found an exception is raised."""
		return self.__barDict[instrument]

	def __contains__(self, instrument):
		"""Returns True if a :class:`pyalgotrade.bar.Bar` for the given instrument is available."""
		return instrument in self.__barDict

	def getInstruments(self):
		"""Returns the instrument symbols."""
		return self.__barDict.keys()

	def getDateTime(self):
		"""Returns the :class:`datetime.datetime` for this set of bars."""
		return self.__dateTime

	def getBar(self, instrument):
		"""Returns the :class:`pyalgotrade.bar.Bar` for the given instrument or None if the instrument is not found."""
		return self.__barDict.get(instrument, None)

def get_open(bar, useAdjusted):
	if useAdjusted:
		return bar.getAdjOpen()
	else:
		return bar.getOpen()

def get_high(bar, useAdjusted):
	if useAdjusted:
		return bar.getAdjHigh()
	else:
		return bar.getHigh()

def get_low(bar, useAdjusted):
	if useAdjusted:
		return bar.getAdjLow()
	else:
		return bar.getLow()

def get_close(bar, useAdjusted):
	if useAdjusted:
		return bar.getAdjClose()
	else:
		return bar.getClose()

