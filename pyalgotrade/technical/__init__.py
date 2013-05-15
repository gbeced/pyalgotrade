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

import collections

from pyalgotrade import dataseries

# Helper class for DataSeries filters that make calculations when new values are added to the
# dataseries they wrap.
class EventWindow:
	def __init__(self, windowSize):
		assert(windowSize > 0)
		self.__values = collections.deque(maxlen=windowSize)
		self.__windowSize = windowSize

	def onNewValue(self, dateTime, value):
		if value != None:
			self.__values.append(value)

	def getValues(self):
		return self.__values

	def getWindowSize(self):
		return self.__windowSize

	def getValue(self):
		raise NotImplementedError()

# Base class for DataSeries filters that make calculations when new values are added to the
# dataseries they wrap. This kind of filters store resulting values.
class EventBasedFilter(dataseries.SequenceDataSeries):
	def __init__(self, dataSeries, eventWindow):
		dataseries.SequenceDataSeries.__init__(self)

		self.__dataSeries = dataSeries
		self.__dataSeries.getNewValueEvent().subscribe(self.__onNewValue)
		self.__eventWindow = eventWindow

	def __onNewValue(self, dataSeries, dateTime, value):
		# Let the event window perform calculations.
		self.__eventWindow.onNewValue(dateTime, value)
		# Get the resulting value
		newValue = self.__eventWindow.getValue()
		# Add the new value.
		self.appendWithDateTime(dateTime, newValue)

	def getDataSeries(self):
		"""Returns the :class:`pyalgotrade.dataseries.DataSeries` being filtered."""
		return self.__dataSeries

# Base class for dataseries views that operate on a set of values.
class DataSeriesFilter(dataseries.DataSeries):
	"""A DataSeriesFilter is a :class:`pyalgotrade.dataseries.DataSeries` instance that decorates another
	:class:`pyalgotrade.dataseries.DataSeries` instance to make some calculations with the values from
	the DataSeries being decorated.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param windowSize: The amount of values to use from the filtered DataSeries to calculate our own values. Must be > 0.
	:type windowSize: int.

	.. note::
		This is a base class and should not be used directly.
	"""

	def __init__(self, dataSeries, windowSize):
		assert(windowSize > 0)
		self.__dataSeries = dataSeries
		self.__windowSize = windowSize
		self.__firstValidPos = (windowSize - 1) + dataSeries.getFirstValidPos()

	def getWindowSize(self):
		"""Returns the window size."""
		return self.__windowSize

	def getFirstValidPos(self):
		return self.__firstValidPos

	def getDataSeries(self):
		"""Returns the :class:`pyalgotrade.dataseries.DataSeries` being wrapped."""
		return self.__dataSeries

	def getLength(self):
		return self.__dataSeries.getLength()

	def getDateTimes(self):
		return self.__dataSeries.getDateTimes()

	def getValueForInvalidPos(self, pos):
		return None

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
			return self.getValueForInvalidPos(pos)
 
		# Check that we have enough values to use
		firstPos = pos - self.__windowSize + 1
		assert(firstPos >= 0)
		ret = self.calculateValue(firstPos, pos)
		return ret

