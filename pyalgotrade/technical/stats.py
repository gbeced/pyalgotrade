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
import numpy

class StdDev(technical.DataSeriesFilter):
	"""Standard deviation filter.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The number of values to use to calculate the Standard deviation.
	:type period: int.
	:param ddof: Delta degrees of freedom.
	:type ddof: int.
	"""

	def __init__(self, dataSeries, period, ddof=0):
		technical.DataSeriesFilter.__init__(self, dataSeries, period)
		self.__ddof = ddof

	def calculateValue(self, firstPos, lastPos):
		ret = None
		values = self.getDataSeries().getValuesAbsolute(firstPos, lastPos)
		if values:
			ret =  numpy.array(values).std(ddof=self.__ddof)
		return ret

