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

from pyalgotrade import technical

import numpy
from scipy import stats

class Slope(technical.DataSeriesFilter):
	"""The Slope filter calculates the slope of the least-squares regression line.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The number of values to use to calculate the slope.
	:type period: int.
	"""

	def __init__(self, dataSeries, period):
		technical.DataSeriesFilter.__init__(self, dataSeries, period)
		self.__x = numpy.array(range(period))

	def getTrendDays(self):
		return self.getWindowSize()

	def calculateValue(self, firstPos, lastPos):
		values = self.getDataSeries().getValuesAbsolute(firstPos, lastPos)
		if values is None:
			return None

		y = numpy.array(values)
		return stats.linregress(self.__x, y)[0]

class Trend(Slope):
	def __init__(self, dataSeries, trendDays, positiveThreshold = 0, negativeThreshold = 0):
		if negativeThreshold > positiveThreshold:
			raise Exception("Invalid thresholds")

		Slope.__init__(self, dataSeries, trendDays)
		self.__positiveThreshold = positiveThreshold
		self.__negativeThreshold = negativeThreshold

	def calculateValue(self, firstPos, lastPos):
		ret = None
		slope = Slope.calculateValue(self, firstPos, lastPos)
		if slope != None:
			if slope > self.__positiveThreshold:
				ret = True
			elif slope < self.__negativeThreshold:
				ret = False
		return ret

