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
from pyalgotrade.utils import collections
from pyalgotrade import warninghelpers

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
	# TODO: Deprecate this.
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
	"""A sequence based :class:`DataSeries`.

	:param values: The values that this DataSeries will hold. If its None, an empty list is used.
	:type values: list.
	:param dateTimes: A list of the :class:`datetime.datetime` associated with each value. If this is not None,
		 it has be the same length as *values*.
	:type dateTimes: list.

	.. note::
		Neither *values* nor *dateTimes* get cloned, and this class takes ownership of them.
	"""

	def __init__(self, values = None, dateTimes = None):
		if values != None:
			self.__values = values
			if dateTimes == None:
				self.__dateTimes = [None for v in self.__values]
			elif len(dateTimes) != len(values):
				raise Exception("The number of datetimes don't match the number of values")
		else:
			self.__values = []
			self.__dateTimes = []

	def __len__(self):
		return len(self.__values)

	def __getitem__(self, key):
		return self.__values[key]

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
		self.appendValueWithDatetime(None, value)

	def appendValueWithDatetime(self, dateTime, value):
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

	def getDateTimes(self):
		return self.__dateTimes

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

	def getDateTimes(self):
		return self.__barDataSeries.getDateTimes()

class BarDataSeries(SequenceDataSeries):
	"""A :class:`DataSeries` of :class:`pyalgotrade.bar.Bar` instances."""

	def __init__(self):
		SequenceDataSeries.__init__(self)

	def appendValue(self, value):
		# Check that bars are appended in order.
		assert(value != None)
		SequenceDataSeries.appendValueWithDatetime(self, value.getDateTime(), value)

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

def datetime_aligned(ds1, ds2):
	"""
	Returns two dataseries that exhibit only those values whose datetimes are in both dataseries.

	:param ds1: A DataSeries instance.
	:type ds1: :class:`DataSeries`
	:param ds2: A DataSeries instance.
	:type ds2: :class:`DataSeries`
	"""
	aligned1 = AlignedDataSeries(ds1)
	aligned2 = AlignedDataSeries(ds2)
	shared = AlignedDataSeriesSharedState(aligned1, aligned2)
	aligned1.setShared(shared)
	aligned2.setShared(shared)
	return (aligned1, aligned2)

class AlignedDataSeriesSharedState:
	def __init__(self, ds1, ds2):
		self.__ds1 = ds1
		self.__ds2 = ds2
		self.__ds1Len = None
		self.__ds2Len = None
		# The position in each of the dataseries for the last intersection
		self.__lastPos1 = None
		self.__lastPos2 = None

	def __isDirty(self):
		if self.__ds1.getDecorated().getLength() != self.__ds1Len:
			return True
		if self.__ds2.getDecorated().getLength() != self.__ds2Len:
			return True
		return False

	def __resetDirty(self):
		# Reset the dirty flag.
		self.__ds1Len = self.__ds1.getDecorated().getLength()
		self.__ds2Len = self.__ds2.getDecorated().getLength()

	def update(self):
		if self.__isDirty():
			# Search for datetime intersections between the data series,
			# but start right after the last one found.
			ds1DateTimes = self.__ds1.getDecorated().getDateTimes()
			ds2DateTimes = self.__ds2.getDecorated().getDateTimes()
			if self.__lastPos1 != None:
				ds1DateTimes = ds1DateTimes[self.__lastPos1+1:]
			if self.__lastPos2 != None:
				ds2DateTimes = ds2DateTimes[self.__lastPos2+1:]

			# Calculate the intersections.
			dateTimes, pos1, pos2 = collections.intersect(ds1DateTimes, ds2DateTimes)

			# Update each array's relative position to make them absolute positions.
			if self.__lastPos1 != None and len(pos1):
				pos1 = [self.__lastPos1 + pos + 1 for pos in pos1]
			if self.__lastPos2 != None and len(pos2):
				pos2 = [self.__lastPos2 + pos + 1 for pos in pos2]

			# Update the last intersection.
			if len(pos1):
				self.__lastPos1 = pos1[-1]
			if len(pos2):
				self.__lastPos2 = pos2[-1]

			# Update the aligned data series.
			self.__ds1.update(dateTimes, pos1)
			self.__ds2.update(dateTimes, pos2)
			self.__resetDirty()

class AlignedDataSeries(DataSeries):
	def __init__(self, ds):
		self.__shared = None
		self.__ds = ds
		self.__dateTimes = []
		self.__positions = []

	def getDecorated(self):
		return self.__ds

	def setShared(self, shared):
		self.__shared = shared

	def update(self, dateTimes, positions):
		assert(len(dateTimes) == len(positions))
		self.__dateTimes.extend(dateTimes)
		self.__positions.extend(positions)

	def getFirstValidPos(self):
		self.__shared.update()
		return 0

	def getLength(self):
		self.__shared.update()
		return len(self.__positions)

	def getValueAbsolute(self, pos):
		self.__shared.update()
		ret = None
		if pos >= 0 and pos < self.getLength():
			ret = self.__ds.getValueAbsolute(self.__positions[pos])
		return ret

	def getDateTimes(self):
		self.__shared.update()
		return self.__dateTimes

