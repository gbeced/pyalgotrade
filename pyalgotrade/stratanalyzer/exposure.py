# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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
.. moduleauthor:: Kimble Young <kbcool@gmail.com>
"""

import math

from pyalgotrade import stratanalyzer
from pyalgotrade import observer
from pyalgotrade import dataseries



#lets you work out the percentage of time (in bars) you have exposure to the market
#this can help with calculating risk adjusted returns or in a portfolio of strategies where a strategy might only make a small annualised return but might average a large return for the time in market - eg  https://en.wikipedia.org/wiki/Santa_Claus_rally
class Exposure(stratanalyzer.StrategyAnalyzer):
	def __init__(self):
		self.__barsInMarket = 0
		self.__totalBars = 0


	def beforeOnBars(self, strat, bars):
		self.__totalBars += 1
		if strat.getBroker().getPositions():
			self.__barsInMarket += 1

	#percent of time we have a market exposure - ie any open positions - eg 0.8
	def getExposurePercent(self):
		try:
			return float(self.__barsInMarket) / float(self.__totalBars)
		except ZeroDivisionError:
			return 0


	def getExposureBars(self):
		return self.__barsInMarket


	def getTotalBars(self):
		return self.__totalBars
