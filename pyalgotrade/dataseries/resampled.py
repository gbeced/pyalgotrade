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

from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from pyalgotrade import barfeed
from pyalgotrade import bar
from pyalgotrade.utils import dt

minute = 60
hour = minute*60
day = hour*24

# frequency in seconds
def get_slot_datetime(dateTime, frequency):
	ts = dt.datetime_to_timestamp(dateTime)
	slot = ts / frequency
	slotTs = (slot + 1) * frequency - 1
	ret = dt.timestamp_to_datetime(slotTs, False)
	if not dt.datetime_is_naive(dateTime):
		ret = dt.localize(ret, dateTime.tzinfo)
	return ret

class Slot:
	def __init__(self, dateTime, bar_):
		self.__dateTime = dateTime
		self.__open = bar_.getOpen()
		self.__high = bar_.getHigh()
		self.__low = bar_.getLow()
		self.__close = bar_.getClose()
		self.__volume = bar_.getVolume()
		self.__adjClose = bar_.getAdjClose()

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

	def getAdjClose(self):
		return self.__adjClose

	def addBar(self, bar_):
		self.__high = max(self.__high, bar_.getHigh())
		self.__low = min(self.__low, bar_.getLow())
		self.__close = bar_.getClose()
		self.__adjClose = bar_.getAdjClose()
		self.__volume += bar_.getVolume()

	def buildBasicBar(self):
		return bar.BasicBar(self.__dateTime, self.__open, self.__high, self.__low, self.__close, self.__volume, self.__adjClose)

class ResampledBarDataSeries(bards.BarDataSeries):
	"""A :class:`pyalgotrade.dataseries.bards.BarDataSeries` that will build on top of another higher frequency :class:`pyalgotrade.dataseries.bards.BarDataSeries`.

	:param dataSeries: The DataSeries instance being resampled.
	:type dataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
	:param frequency: The grouping frequency.
	:param maxLen: The maximum number of values to hold. If not None, it must be greater than 0.
		Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
	:type maxLen: int.

	.. note::
		* Valid **frequency** parameter values are:

		 * pyalgotrade.barfeed.Frequency.MINUTE
		 * pyalgotrade.barfeed.Frequency.HOUR
		 * pyalgotrade.barfeed.Frequency.DAY
	"""

	def __init__(self, dataSeries, frequency, maxLen=dataseries.DEFAULT_MAX_LEN):
		bards.BarDataSeries.__init__(self, maxLen)

		if not isinstance(dataSeries, bards.BarDataSeries):
			raise Exception("dataSeries must be a dataseries.bards.BarDataSeries instance")

		if frequency == barfeed.Frequency.MINUTE:
			 self.__frequency = minute
		elif frequency == barfeed.Frequency.HOUR:
			 self.__frequency = hour
		elif frequency == barfeed.Frequency.DAY:
			 self.__frequency = day
		else:
			raise Exception("Invalid frequency")

		self.__slot = None
		dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

	def pushLast(self):
		if self.__slot != None:
			self.appendWithDateTime(self.__slot.getDateTime(), self.__slot.buildBasicBar())
		self.__slot = None

	def __onNewValue(self, dataSeries, dateTime, value):
		dateTime = get_slot_datetime(value.getDateTime(), self.__frequency)

		if self.__slot == None:
			self.__slot = Slot(dateTime, value)
		elif self.__slot.getDateTime() == dateTime:
			self.__slot.addBar(value)
		else:
			self.appendWithDateTime(self.__slot.getDateTime(), self.__slot.buildBasicBar())
			self.__slot = Slot(dateTime, value)

