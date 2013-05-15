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

from pyalgotrade import warninghelpers
from pyalgotrade import observer

# It is important to inherit object to get __getitem__ to work properly.
# Check http://code.activestate.com/lists/python-list/621258/
class DataSeries(object):
	"""Base class for data series. A data series is an abstraction used to manage historical data.

	.. note::
		This is a base class and should not be used directly.
	"""

	def __len__(self):
		"""Returns the number of elements in the data series."""
		return self.getLength()

	def __getitem__(self, key):
		"""Returns the value at a given position/slice. It raises IndexError if the position is invalid,
		or TypeError if the key type is invalid."""
		if isinstance(key, slice):
			return [self[i] for i in xrange(*key.indices(self.getLength()))]
		elif isinstance(key, int) :
			if key < 0:
				key += self.getLength()
			if key >= self.getLength() or key < 0:
				raise IndexError("Index out of range")
			return self.getValueAbsolute(key)
		else:
			raise TypeError("Invalid argument type")

	def getFirstValidPos(self):
		raise NotImplementedError()

	def getLength(self):
		raise NotImplementedError()

	# This is similar to __getitem__ for ints, but it shouldn't raise for invalid positions.
	def getValueAbsolute(self, pos):
		raise NotImplementedError()

	def getDateTimes(self):
		"""Returns a list of :class:`datetime.datetime` associated with each value."""
		raise NotImplementedError()

	# Returns a sequence of absolute values [firstPos, lastPos].
	# if includeNone is False and at least one value is None, then None is returned.
	def getValuesAbsolute(self, firstPos, lastPos, includeNone = False):
		# Deprecated since 0.13
		warninghelpers.deprecation_warning("getValuesAbsolute will be deprecated in the next version. Please use [] instead.", stacklevel=2)
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
		# Deprecated since 0.12
		warninghelpers.deprecation_warning("getValues will be deprecated in the next version. Please use [] instead.", stacklevel=2)
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
		# Deprecated since 0.12
		warninghelpers.deprecation_warning("getValue will be deprecated in the next version. Please use [] instead.", stacklevel=2)
		ret = None
		absolutePos = self.__mapRelativeToAbsolute(valuesAgo)
		if absolutePos != None:
			ret = self.getValueAbsolute(absolutePos)
		return ret

class SequenceDataSeries(DataSeries):
	"""A :class:`DataSeries` that holds values in a sequence in memory."""

	def __init__(self):
		self.__newValueEvent = observer.Event()
		self.__values = []
		self.__dateTimes = []

	def __len__(self):
		return len(self.__values)

	def __getitem__(self, key):
		return self.__values[key]

	# Event handler receives:
	# 1: Dataseries generating the event
	# 2: The datetime for the new value
	# 3: The new value
	def getNewValueEvent(self):
		return self.__newValueEvent

	def getFirstValidPos(self):
		return 0

	def getLength(self):
		return len(self.__values)

	def getValueAbsolute(self, pos):
		ret = None
		if pos >= 0 and pos < len(self.__values):
			ret = self.__values[pos]
		return ret

	def append(self, value):
		"""Appends a value."""
		self.appendWithDateTime(None, value)

	def appendValue(self, value):
		# Deprecated since 0.13
		warninghelpers.deprecation_warning("appendValue will be deprecated in the next version. Please use append instead.", stacklevel=2)
		self.append(value)

	def appendWithDateTime(self, dateTime, value):
		"""
		Appends a value with an associated datetime.

		.. note::
			If dateTime is not None, it must be greater than the last one.
		"""
		if dateTime != None and len(self.__dateTimes) != 0 and self.__dateTimes[-1] >= dateTime:
			raise Exception("Invalid datetime. It must be bigger than that last one")
		self.__dateTimes.append(dateTime)
		self.__values.append(value)
		assert(len(self.__values) == len(self.__dateTimes))

		self.getNewValueEvent().emit(self, dateTime, value)

	def appendValueWithDatetime(self, dateTime, value):
		# Deprecated since 0.13
		warninghelpers.deprecation_warning("appendValueWithDatetime will be deprecated in the next version. Please use appendWithDateTime instead.", stacklevel=2)
		self.appendWithDateTime(dateTime, value)

	def getDateTimes(self):
		return self.__dateTimes

	def getValues(self):
		return self.__values

def datetime_aligned(ds1, ds2):
	"""
	Returns two dataseries that exhibit only those values whose datetimes are in both dataseries.

	:param ds1: A DataSeries instance.
	:type ds1: :class:`DataSeries`
	:param ds2: A DataSeries instance.
	:type ds2: :class:`DataSeries`
	"""
	aligned1 = SequenceDataSeries()
	aligned2 = SequenceDataSeries()
	Syncer(ds1, ds2, aligned1, aligned2)
	return (aligned1, aligned2)

# This class is responsible for filling 2 dataseries when 2 other dataseries get new values.
class Syncer:
	def __init__(self, sourceDS1, sourceDS2, destDS1, destDS2):
		self.__sourceDS1 = sourceDS1
		self.__sourceDS2 = sourceDS2
		self.__destDS1 = destDS1
		self.__destDS2 = destDS2
		sourceDS1.getNewValueEvent().subscribe(self.__onNewValue1)
		sourceDS2.getNewValueEvent().subscribe(self.__onNewValue2)
		# Source dataseries will keep a reference to self and that will prevent from getting this destroyed.

	# Scan backwards for the position of dateTime in ds.
	def __findPosForDateTime(self, ds, dateTime):
		ret = None
		dateTimes = ds.getDateTimes()
		i = len(ds) - 1
		while i >= 0:
			if dateTimes[i] == dateTime:
				ret = i
				break
			elif dateTimes[i] < dateTime:
				break
			i -= 1
		return ret

	def __onNewValue1(self, dataSeries, dateTime, value):
		pos2 = self.__findPosForDateTime(self.__sourceDS2, dateTime)
		# If a value for dateTime was added to self.__sourceDS1, and a value for that same datetime is also in self.__sourceDS2
		# then append to both destination dataseries.
		if pos2 != None:
			self.__append(dateTime, value, self.__sourceDS2[pos2])

	def __onNewValue2(self, dataSeries, dateTime, value):
		pos1 = self.__findPosForDateTime(self.__sourceDS1, dateTime)
		# If a value for dateTime was added to self.__sourceDS2, and a value for that same datetime is also in self.__sourceDS1
		# then append to both destination dataseries.
		if pos1 != None:
			self.__append(dateTime, self.__sourceDS1[pos1], value)

	def __append(self, dateTime, value1, value2):
		self.__destDS1.appendWithDateTime(dateTime, value1)
		self.__destDS2.appendWithDateTime(dateTime, value2)

