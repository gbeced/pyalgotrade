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
from pyalgotrade import bar

class BarValueDataSeries(dataseries.DataSeries):
	def __init__(self, barDataSeries, barMethod):
		self.__barDataSeries = barDataSeries
		self.__barMethod = barMethod

	def supportsCaching(self):
		return self.__barDataSeries.supportsCaching()

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

class BarDataSeries(dataseries.SequenceDataSeries):
	"""A :class:`pyalgotrade.dataseries.DataSeries` of :class:`pyalgotrade.bar.Bar` instances."""

	def __init__(self):
		dataseries.SequenceDataSeries.__init__(self)

	def appendValue(self, value):
		# Check that bars are appended in order.
		assert(value != None)
		dataseries.SequenceDataSeries.appendValueWithDatetime(self, value.getDateTime(), value)

	def getOpenDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the open prices."""
		return BarValueDataSeries(self, bar.Bar.getOpen)

	def getCloseDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the close prices."""
		return BarValueDataSeries(self, bar.Bar.getClose)

	def getHighDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the high prices."""
		return BarValueDataSeries(self, bar.Bar.getHigh)

	def getLowDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the low prices."""
		return BarValueDataSeries(self, bar.Bar.getLow)

	def getVolumeDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the volume."""
		return BarValueDataSeries(self, bar.Bar.getVolume)

	def getAdjCloseDataSeries(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted close prices."""
		return BarValueDataSeries(self, bar.Bar.getAdjClose)

