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

class DrawDownHelper:
	def __init__(self, initialValue):
		self.__highWatermark = initialValue
		self.__lowWatermark = initialValue
		self.__lastValue = initialValue
		self.__duration = 0

	# The drawdown duration, not necessarily the max drawdown duration.
	def getDuration(self):
		return self.__duration

	def getMaxDrawDown(self):
		return (self.__lowWatermark - self.__highWatermark) / float(self.__highWatermark)

	def getCurrentDrawDown(self):
		return (self.__lastValue - self.__highWatermark) / float(self.__highWatermark)

	def update(self, value):
		self.__lastValue = value
		if value < self.__highWatermark:
			self.__duration += 1
			self.__lowWatermark = min(self.__lowWatermark, value)
		else:
			self.__highWatermark = value
			self.__lowWatermark = value
			self.__duration = 0

class DrawDown(stratanalyzer.StrategyAnalyzer):
	"""A :class:`pyalgotrade.stratanalyzer.StrategyAnalyzer` that calculates
	max. drawdown and longest drawdown duration for the portfolio."""

	def __init__(self):
		self.__maxDD = 0
		self.__longestDDDuration = 0
		self.__currDrawDown = None

	def attached(self, strat):
		self.__currDrawDown = DrawDownHelper(self.calculateEquity(strat))

	def calculateEquity(self, strat):
		return strat.getBroker().getEquity()

		ret = strat.getBroker().getCash()

		for instrument, shares in strat.getBroker().getPositions().iteritems():
			_bar = strat.getFeed().getLastBar(instrument)
			if shares > 0:
				ret += strat.getBroker().getBarClose(_bar) * shares
			elif shares < 0:
				ret += strat.getBroker().getBarClose(_bar) * shares
		return ret

	def beforeOnBars(self, strat):
		equity = self.calculateEquity(strat)
		self.__currDrawDown.update(equity)
		self.__longestDDDuration = max(self.__longestDDDuration, self.__currDrawDown.getDuration())
		self.__maxDD = min(self.__maxDD, self.__currDrawDown.getMaxDrawDown())

	def getMaxDrawDown(self):
		"""Returns the max. (deepest) drawdown."""
		return abs(self.__maxDD)

	def getLongestDrawDownDuration(self):
		"""Returns the duration of the longest drawdown.

		.. note::
			Note that this is the duration of the longest drawdown, not necessarily the deepest one.
		"""	
		return self.__longestDDDuration

