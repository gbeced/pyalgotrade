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
from pyalgotrade.technical import ma
from pyalgotrade.technical import stats

class Band(technical.DataSeriesFilter):
	def __init__(self, middleBandDS, priceDS, n, k):
		technical.DataSeriesFilter.__init__(self, middleBandDS, 1)
		self.__stdDev = stats.StdDev(priceDS, n)
		self.__k = k

	def calculateValue(self, firstPos, lastPos):
		assert(firstPos == lastPos)
		ret = None
		value = self.getDataSeries().getValueAbsolute(firstPos)
		if value != None:
			ret = value + self.__stdDev.getValueAbsolute(firstPos) * self.__k
		return ret

class BollingerBands:
	"""Bollinger Bands filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:bollinger_bands.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The number of values to use in the calculation. Must be > 1.
	:type period: int.
	:param numStdDev: The number of standard deviations to use for the upper and lower bands.
	:type numStdDev: int.
	"""

	def __init__(self, dataSeries, period, numStdDev):
		self.__middleBand = ma.SMA(dataSeries, period)
		self.__upperBand = Band(self.__middleBand, dataSeries, period, numStdDev)
		self.__lowerBand = Band(self.__middleBand, dataSeries, period, numStdDev*-1)

	def getUpperBand(self):
		"""
		Returns the upper band as a :class:`pyalgotrade.dataseries.DataSeries`.
		"""
		return self.__upperBand

	def getMiddleBand(self):
		"""
		Returns the middle band as a :class:`pyalgotrade.dataseries.DataSeries`.
		"""
		return self.__middleBand

	def getLowerBand(self):
		"""
		Returns the lower band as a :class:`pyalgotrade.dataseries.DataSeries`.
		"""
		return self.__lowerBand

