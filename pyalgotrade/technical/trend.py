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
from pyalgotrade import dataseries

import numpy

def linear_regression(values):
	y = values
	xi = numpy.arange(0, len(values))
	A = numpy.array([ xi, numpy.ones(len(values))])
	w = numpy.linalg.lstsq(A.T, y)[0]
	return w

class SlopeEventWindow(technical.EventWindow):
	def __init__(self, windowSize):
		technical.EventWindow.__init__(self, windowSize)
		self.__x = numpy.array(range(windowSize))

	def getValue(self):
		ret = None
		if self.windowFull():
			y = numpy.array(self.getValues())
			ret = linear_regression(y)[0]
		return ret

class Slope(technical.EventBasedFilter):
	"""The Slope filter calculates the slope of the least-squares regression line.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The number of values to use to calculate the slope.
	:type period: int.
	:param maxLen: The maximum number of values to hold. If not None, it must be greater than 0.
		Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
	:type maxLen: int.
	"""

	def __init__(self, dataSeries, period, maxLen=dataseries.DEFAULT_MAX_LEN):
		technical.EventBasedFilter.__init__(self, dataSeries, SlopeEventWindow(period), maxLen)

	def getTrendDays(self):
		return self.getWindowSize()

class TrendEventWindow(SlopeEventWindow):
	def __init__(self, windowSize, positiveThreshold, negativeThreshold):
		if negativeThreshold > positiveThreshold:
			raise Exception("Invalid thresholds")

		SlopeEventWindow.__init__(self, windowSize)
		self.__positiveThreshold = positiveThreshold
		self.__negativeThreshold = negativeThreshold
	
	def getValue(self):
		ret = SlopeEventWindow.getValue(self)
		if ret != None:
			if ret > self.__positiveThreshold:
				ret = True
			elif ret < self.__negativeThreshold:
				ret = False
			else: # Between negative and postive thresholds.
				ret = None
		return ret

class Trend(technical.EventBasedFilter):
	def __init__(self, dataSeries, trendDays, positiveThreshold=0, negativeThreshold=0, maxLen=dataseries.DEFAULT_MAX_LEN):
		technical.EventBasedFilter.__init__(self, dataSeries, TrendEventWindow(trendDays, positiveThreshold, negativeThreshold), maxLen)

