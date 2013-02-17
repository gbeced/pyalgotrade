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

from pyalgotrade import technical
from pyalgotrade import dataseries

class VWAP(technical.DataSeriesFilter):
	"""Volume Weighted Average Price filter.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.BarDataSeries`.
	:param period: The number of values to use to calculate the VWAP.
	:type period: int.
	:param useTypicalPrice: True if the typical price should be used instead of the closing price.
	:type useTypicalPrice: boolean.

	"""

	def __init__(self, dataSeries, period, useTypicalPrice=False):
		if not isinstance(dataSeries, dataseries.BarDataSeries):
			raise Exception("dataSeries must be a dataseries.BarDataSeries instance")
		technical.DataSeriesFilter.__init__(self, dataSeries, period)
		self.__useTypicalPrice = useTypicalPrice

	def getPeriod(self):
		return self.getWindowSize()

	def calculateValue(self, firstPos, lastPos):
		cumTotal = 0
		cumVolume = 0

		for i in xrange(firstPos, lastPos+1):
			bar = self.getDataSeries().getValueAbsolute(i)
			if bar is None:
				return None
			if self.__useTypicalPrice:
				cumTotal += bar.getTypicalPrice() * bar.getVolume()
			else:
				cumTotal += bar.getClose() * bar.getVolume()
			cumVolume += bar.getVolume()

		return cumTotal / float(cumVolume)

