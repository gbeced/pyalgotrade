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

from pyalgotrade import stratanalyzer
from pyalgotrade.stratanalyzer import returns

class DrawDown(stratanalyzer.StrategyAnalyzer):
	"""A max. drawdown and max. drawdown duration :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer`."""

	def __init__(self):
		self.__highWatermark = None
		self.__maxDrawDown = 0
		self.__lastDrawDuration = 0
		self.__maxDrawDuration = 0

	def beforeAttach(self, strat):
		# Get or create a shared ReturnsAnalyzerBase
		analyzer = returns.ReturnsAnalyzerBase.getOrCreateShared(strat)
		analyzer.getEvent().subscribe(self.__onReturns)

	def __onReturns(self, returnsAnalyzerBase, bars):
		cumulativeReturn = returnsAnalyzerBase.getCumulativeReturn()
		self.__highWatermark = max(self.__highWatermark, cumulativeReturn)
		drawDown = (1 + cumulativeReturn) / float(1 + self.__highWatermark) - 1

		# Calculate max drawdown duration
		if drawDown == 0:
			self.__lastDrawDuration = 0
		else:
			self.__lastDrawDuration += 1
		self.__maxDrawDuration = max(self.__maxDrawDuration, self.__lastDrawDuration)

		# Calculate max drawdown.
		self.__maxDrawDown = min(self.__maxDrawDown, drawDown) 

	def getMaxDrawDown(self):
		"""Returns the max. drawdown."""
		return abs(self.__maxDrawDown)

	def getMaxDrawDownDuration(self):
		"""Returns the max. drawdown duration."""
		return self.__maxDrawDuration

