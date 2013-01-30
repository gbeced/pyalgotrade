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

def compute_diff(values1, values2):
	assert(len(values1) == len(values2))
	ret = []
	for i in range(len(values1)):
		v1 = values1[i]
		v2 = values2[i]
		if v1 != None and v2 != None:
			diff = v1 - v2
		else:
			diff = None
		ret.append(diff)
	return ret

def positive(value):
	return value > 0

def negative(value):
	return value < 0

class Base(technical.TechnicalIndicatorBase):
	def __init__(self, ds1, ds2, period, signCheck):
		assert(period > 1)
		technical.TechnicalIndicatorBase.__init__(self, 1)
		self.__ds1 = ds1
		self.__ds2 = ds2
		self.__period = period
		self.__signCheck = signCheck

	def getDateTimes(self):
		# I'm using self.__ds1 because this is basically a wrapper on top of the first dataseries.
		return self.__ds1.getDateTimes()

	def getFirstValidPos(self):
		return max(self.__ds1.getFirstValidPos(), self.__ds2.getFirstValidPos())

	def getLength(self):
		# I'm using self.__ds1 because this is basically a wrapper on top of the first dataseries.
		return self.__ds1.getLength()

	def calculateValue(self, firstPos, lastPos):
		# Get both set of values.
		firstPos = max(lastPos - (self.__period - 1), 0)
		valuesDS1 = self.__ds1.getValuesAbsolute(firstPos, lastPos, True)
		valuesDS2 = self.__ds2.getValuesAbsolute(firstPos, lastPos, True)

		# Compute differences and check sign changes.
		ret = 0
		diffs = compute_diff(valuesDS1, valuesDS2)
		prevDiff = None
		for diff in diffs:
			if prevDiff != None and not self.__signCheck(prevDiff) and self.__signCheck(diff):
				ret += 1
			prevDiff = diff
		return ret

class CrossAbove(Base):
	"""Checks for a cross above conditions over the specified period between two DataSeries objects.

	It returns the number of times ds1 crossed above ds2 during the given period.

	:param ds1: The DataSeries that crosses.
	:type ds1: :class:`pyalgotrade.dataseries.DataSeries`.
	:param ds2: The DataSeries being crossed.
	:type ds2: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: Max number of values to check for cross above conditions. Must be > 1.
	:type period: int.
	"""

	def __init__(self, ds1, ds2, period = 2):
		Base.__init__(self, ds1, ds2, period, positive)

class CrossBelow(Base):
	"""Checks for a cross below conditions over the specified period between two DataSeries objects.

	It returns the number of times ds1 crossed below ds2 during the given period.

	:param ds1: The DataSeries that crosses.
	:type ds1: :class:`pyalgotrade.dataseries.DataSeries`.
	:param ds2: The DataSeries being crossed.
	:type ds2: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: Max number of values to check for cross below conditions. Must be > 1.
	:type period: int.
	"""

	def __init__(self, ds1, ds2, period = 2):
		Base.__init__(self, ds1, ds2, period, negative)

