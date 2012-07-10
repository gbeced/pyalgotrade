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

import bar

class DataSeries:
	"""Base class for data series. A data series is an abstraction used to manage historical data.

		.. note::
			This is a base class and should not be used directly.
	"""

	def getFirstValidPos(self):
		"""Returns the first valid position in the dataseries."""
		raise Exception("Not implemented")

	def getLength(self):
		"""Returns the number of values in the data series."""
		raise Exception("Not implemented")

	def getValueAbsolute(self, pos):
		"""Returns the value at a given instant, or None if the value doesn't exist.

		:param pos: The absolute position of the value in the dataseries. Must be >= 0.
		:type valuesAgo: int

		* getValueAbsolute(0) returns the first value.
		* getValueAbsolute(1) returns the second value.
		"""
		raise Exception("Not implemented")

	# Returns a sequence of absolute values [firstPos, lastPos].
	# if includeNone is False and at least one value is None, then None is returned.
	def getValuesAbsolute(self, firstPos, lastPos, includeNone = False):
		ret = []
		for i in xrange(firstPos, lastPos+1):
			value = self.getValueAbsolute(i)
			if value is None and not includeNone:
				return None
			ret.append(value)
		return ret

	def __mapRelativeToAbsolute(self, valuesAgo):
		if valuesAgo < 0:
			return None

		ret = self.getLength() - valuesAgo - 1
		if ret < self.getFirstValidPos():
			ret = None
		return ret

	def getValues(self, count, valuesAgo = 0, includeNone = False):
		"""Returns a list of values at a given instant, relative to the last value.

		:param count: The max number of values to return. Must be >= 0.
		:type count: int
		:param valuesAgo: The position of the value relative to the last one. Must be >= 0.
		:type valuesAgo: int
		:param includeNone: True if None values should be included. If False, and any of the values are None, None is returned.
		:type includeNone: boolean

		* getValues(2) returns the last 2 values.
		* getValues(2, 1) returns the antepenultimate and penultimate values (assuming that the dataseries has at least 3 values).
		"""

		if count <= 0:
			return None

		absolutePos = self.__mapRelativeToAbsolute(valuesAgo + (count - 1))
		if absolutePos == None:
			return None

		ret = []
		for i in xrange(count):
			value = self.getValueAbsolute(absolutePos + i)
			if value is None and not includeNone:
				return None
			ret.append(value)
		return ret

	def getValue(self, valuesAgo = 0):
		"""Returns the value at a given instant, relative to the last value, or None if the value doesn't exist.

		:param valuesAgo: The position of the value relative to the last one. Must be >= 0.
		:type valuesAgo: int

		* getValue() returns the last value.
		* getValue(1) returns the previous value (assuming that the dataseries has at least 2 values).
		"""

		ret = None
		absolutePos = self.__mapRelativeToAbsolute(valuesAgo)
		if absolutePos != None:
			ret = self.getValueAbsolute(absolutePos)
		return ret

class SequenceDataSeries(DataSeries):
	"""A sequence based :class:`DataSeries`.

	:param values: The values that this DataSeries will hold. If its None, an empty list is used. **Note that the list is not cloned and it takes ownership of it**.
	:type values: list.
	"""

	def __init__(self, values = None):
		if values != None:
			self.__values = values
		else:
			self.__values = []

	def getFirstValidPos(self):
		return 0

	def getLength(self):
		return len(self.__values)

	def getValueAbsolute(self, pos):
		ret = None
		if pos >= 0 and pos < len(self.__values):
			ret = self.__values[pos]
		return ret

	def appendValue(self, value):
		"""Appends a value."""
		self.__values.append(value)

class BarValueDataSeries(DataSeries):
	def __init__(self, barDataSeries, barMethod):
		self.__barDataSeries = barDataSeries
		self.__barMethod = barMethod

	def getFirstValidPos(self):
		return self.__barDataSeries.getFirstValidPos()

	def getLength(self):
		return self.__barDataSeries.getLength()

	def getValueAbsolute(self, pos):
		ret = self.__barDataSeries.getValueAbsolute(pos)
		if ret != None:
			ret = self.__barMethod(ret)
		return ret

class BarDataSeries(SequenceDataSeries):
	"""A :class:`DataSeries` of :class:`pyalgotrade.bar.Bar` instances."""

	def __init__(self):
		SequenceDataSeries.__init__(self)
		self.__lastDatetime = None

	def appendValue(self, value):
		# Check that bars are appended in order.
		assert(value != None)
		if self.__lastDatetime != None and value.getDateTime() <= self.__lastDatetime:
			raise Exception("Invalid bar datetime. It must be bigger than that last one")
		self.__lastDatetime = value.getDateTime()
		SequenceDataSeries.appendValue(self, value)

	def getOpenDataSeries(self):
		"""Returns a :class:`DataSeries` with the open prices."""
		return BarValueDataSeries(self, bar.Bar.getOpen)

	def getCloseDataSeries(self):
		"""Returns a :class:`DataSeries` with the close prices."""
		return BarValueDataSeries(self, bar.Bar.getClose)

	def getHighDataSeries(self):
		"""Returns a :class:`DataSeries` with the high prices."""
		return BarValueDataSeries(self, bar.Bar.getHigh)

	def getLowDataSeries(self):
		"""Returns a :class:`DataSeries` with the low prices."""
		return BarValueDataSeries(self, bar.Bar.getLow)

	def getVolumeDataSeries(self):
		"""Returns a :class:`DataSeries` with the volume."""
		return BarValueDataSeries(self, bar.Bar.getVolume)

	def getAdjCloseDataSeries(self):
		"""Returns a :class:`DataSeries` with the adjusted close prices."""
		return BarValueDataSeries(self, bar.Bar.getAdjClose)

