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

class Bar:
	"""An instrument's prices at a given time.

	:param dateTime: The date time.
	:type dateTime: datetime.datetime
	:param open_: The opening price.
	:type open_: float
	:param high: The highest price.
	:type high: float
	:param low: The lowest price.
	:type low: float
	:param close: The closing price.
	:type close: float
	:param volume: The volume.
	:type volume: float
	:param close: The adjusted closing price.
	:type close: float
	"""

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

	# datetime in UTC.
	def getDateTime(self):
		"""Returns the :class:`datetime.datetime`."""
		return self.__dateTime

	def getOpen(self):
		"""Returns the opening price."""
		return self.__open

	def getHigh(self):
		"""Returns the highest price."""
		return self.__high

	def getLow(self):
		"""Returns the lowest price."""
		return self.__low

	def getClose(self):
		"""Returns the closing price."""
		return self.__close

	def getVolume(self):
		"""Returns the volume."""
		return self.__volume

	def getAdjOpen(self):
		return self.__adjClose * self.__open / float(self.__close)

	def getAdjHigh(self):
		return self.__adjClose * self.__high / float(self.__close)

	def getAdjLow(self):
		return self.__adjClose * self.__low / float(self.__close)

	def getAdjClose(self):
		"""Returns the adjusted closing price."""
		return self.__adjClose

	def getSessionClose(self):
		"""Returns True if this is the last bar for the session, or False otherwise."""
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

	def getInstruments(self):
		"""Returns the instrument symbols."""
		return self.__barDict.keys()

	def getDateTime(self):
		"""Returns the :class:`datetime.datetime` for this set of bars."""
		return self.__dateTime

	def getBar(self, instrument):
		"""Returns the :class:`pyalgotrade.bar.Bar` for the given instrument or None if the instrument is not found."""
		ret = None
		try:
			ret = self.__barDict[instrument]
		except KeyError:
			pass
		return ret

