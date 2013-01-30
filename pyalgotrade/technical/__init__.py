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

class TechnicalIndicatorBase(dataseries.DataSeries):
	def __init__(self, windowSize, cacheSize=512):
		assert(windowSize > 0)
		self.__windowSize = windowSize
		self.__cache = Cache(cacheSize)

	def getCache(self):
		return self.__cache

	def getWindowSize(self):
		"""Returns the window size."""
		return self.__windowSize

	# Override to implement filtering logic. Should never be called directly.
	# firstPos <= lastPos
	def calculateValue(self, firstPos, lastPos):
		"""This method has to be overriden to add the filtering logic and return a new value.

		:param firstPos: Absolute position for the first value to use from the DataSeries being filtered.
		:type firstPos: int.
		:param lastPos: Absolute position for the last value to use from the DataSeries being filtered.
		:type lastPos: int.
		"""
		raise Exception("Not implemented")

	def getValueAbsolute(self, pos):
		# Check that there are enough values to calculate this (given the current window size and the nested ones).
		if pos < self.getFirstValidPos() or pos >= self.getLength():
			return None
 
		# Check that we have enough values to use
		firstPos = pos - self.__windowSize + 1
		assert(firstPos >= 0)
 
		# Try to get the value from the cache.
		if self.getCache().isCached(pos):
			ret = self.getCache().getValue(pos)
		else:
			ret = self.calculateValue(firstPos, pos)
			# Avoid caching None's in case a invalid pos is requested that becomes valid in the future.
			if ret != None:
				self.getCache().putValue(pos, ret)
		return ret

class DataSeriesFilter(TechnicalIndicatorBase):
	"""A DataSeriesFilter is a :class:`pyalgotrade.dataseries.DataSeries` instance that decorates another :class:`pyalgotrade.dataseries.DataSeries` instance
	to make some calculations with the values from the DataSeries being decorated.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param windowSize: The amount of values to use from the filtered DataSeries to calculate our own values. Must be > 0.
	:type windowSize: int.
	:param cacheSize: The values that this filter calculates will be cached so they don't have to be calculated twice. This parameter controls how many results will be kept in the cache.
	:type cacheSize: int.

	.. note::
		This is a base class and should not be used directly.
	"""
	def __init__(self, dataSeries, windowSize, cacheSize=512):
		TechnicalIndicatorBase.__init__(self, windowSize, cacheSize)
		self.__dataSeries = dataSeries

	def getFirstValidPos(self):
		return (self.getWindowSize() - 1) + self.__dataSeries.getFirstValidPos()

	def getDataSeries(self):
		"""Returns the :class:`pyalgotrade.dataseries.DataSeries` being filtered."""
		return self.__dataSeries

	def getLength(self):
		return self.__dataSeries.getLength()

	def getDateTimes(self):
		return self.__dataSeries.getDateTimes()

# Cache with FIFO replacement policy.
class Cache:
	def __init__(self, size):
		assert(size > 0)
		self.__size = size
		self.__cache = {}
		self.__pos = []

	def isCached(self, pos):
		return pos in self.__cache

	def getValue(self, pos):
		return self.__cache.get(pos)

	def putValue(self, pos, value):
		self.__cache[pos] = value
		self.__pos.append(pos)

		# Free up an entry if necessary
		if len(self.__cache) > self.__size:
			del self.__cache[ self.__pos.pop(0) ]

