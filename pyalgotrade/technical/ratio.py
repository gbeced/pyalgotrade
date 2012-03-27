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
from pyalgotrade import utils

# Calculates the ratio between a value and the previous one.
# The ratio can't be calculated if a previous value is 0.
class Ratio(technical.DataSeriesFilter):
	def __init__(self, dataSeries):
		technical.DataSeriesFilter.__init__(self, dataSeries, 2)

	def calculateValue(self, firstPos, lastPos):
		prev = self.getDataSeries().getValueAbsolute(firstPos)
		actual = self.getDataSeries().getValueAbsolute(lastPos)

		if actual is None or prev is None or prev == 0:
			return None

		return utils.get_change_percentage(actual, prev)

