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

import numpy

class StdDevEventWindow(technical.EventWindow):
	def __init__(self, period, ddof):
		assert(period > 0)
		technical.EventWindow.__init__(self, period)
		self.__ddof = ddof

	def getValue(self):
		ret = None
		if self.windowFull():
			ret =  numpy.array(self.getValues()).std(ddof=self.__ddof)
		return ret

class StdDev(technical.EventBasedFilter):
	"""Standard deviation filter.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The number of values to use to calculate the Standard deviation.
	:type period: int.
	:param ddof: Delta degrees of freedom.
	:type ddof: int.
	:param maxLen: The maximum number of values to hold. If not None, it must be greater than 0.
		Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
	:type maxLen: int.
	"""

	def __init__(self, dataSeries, period, ddof=0, maxLen=dataseries.DEFAULT_MAX_LEN):
		technical.EventBasedFilter.__init__(self, dataSeries, StdDevEventWindow(period, ddof), maxLen)

