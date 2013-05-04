# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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
import collections

class BoundedDataSeries(dataseries.DataSeries):
	def __init__(self, maxSize):
		assert(maxSize > 0)
		self.__values = collections.deque(maxlen=maxSize)
		self.__dateTimes = collections.deque(maxlen=maxSize)

	def __len__(self):
		return len(self.__values)

	def __getitem__(self, key):
		"""Returns the value at a given position/slice. It raises IndexError if the position is invalid,
		or TypeError if the key type is invalid."""
		if isinstance(key, slice):
			return [self[i] for i in xrange(*key.indices(len(self.__values)))]
		elif isinstance(key, int) :
			if key < 0:
				key += len(self.__values)
			if key >= len(self.__values) or key < 0:
				raise IndexError("Index out of range")
			return self.__values[key]
		else:
			raise TypeError("Invalid argument type")

	def supportsCaching(self):
		return False

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

	def getDateTimes(self):
		return self.__dateTimes

