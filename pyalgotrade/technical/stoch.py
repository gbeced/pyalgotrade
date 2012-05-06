# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

def get_low_high_values(bars):
	currBar = bars[0]
	lowestLow = currBar.getLow()
	highestHigh = currBar.getHigh()
	for i in range(len(bars)):
		currBar = bars[i]
		lowestLow = min(lowestLow, currBar.getLow())
		highestHigh = max(highestHigh, currBar.getHigh())
	return (lowestLow, highestHigh)

class StochasticOscillator(technical.DataSeriesFilter):
	"""Stochastic Oscillator filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:stochastic_oscillato.
	Note that the value returned by this filter is %K. To access %D use :meth:`getD`.

	:param barDataSeries: The BarDataSeries instance being filtered.
	:type barDataSeries: :class:`pyalgotrade.dataseries.BarDataSeries`.
	:param period: The period. Must be > 1.
	:type period: int.
	:param dSMAPeriod: The %D SMA period. Must be > 1.
	:type dSMAPeriod: int.
	"""

	def __init__(self, barDataSeries, period, dSMAPeriod = 3):
		assert(period > 1)
		assert(dSMAPeriod > 1)
		technical.DataSeriesFilter.__init__(self, barDataSeries, period)
		self.__d = ma.SMA(self, dSMAPeriod)

	def calculateValue(self, firstPos, lastPos):
		bars = self.getDataSeries().getValuesAbsolute(firstPos, lastPos)
		if bars == None:
			return None

		lowestLow, highestHigh = get_low_high_values(bars)
		currentClose = bars[-1].getClose()
		return (currentClose - lowestLow) / float(highestHigh - lowestLow) * 100

	def getD(self):
		"""Returns a :class:`pyalgotrade.dataseries.DataSeries` with the %D values."""
		return self.__d

