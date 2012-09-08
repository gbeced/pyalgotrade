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

class ReturnsAnalyzer(stratanalyzer.StrategyAnalyzer):
	def __init__(self):
		self.__prevAdjClose = {} # Prev. adj. close per instrument
		self.__shares = {} # Shares at the end of the period (bar).
		self.__cumRet = 0
		self.__firstBarProcessed = False

	def onReturns(self, bars, netReturn, cumulativeReturn):
		raise NotImplementedError()

	def __calculateReturns(self, bars):
		count = 0
		returns = 0

		# Calculate net return for each of the shares that were available at the end of the previous bar.
		for instrument, shares in self.__shares.iteritems():
			try:
				bar = bars.getBar(instrument)
				if bar == None or shares == 0:
					continue

				currAdjClose = bar.getAdjClose()
				prevAdjClose = self.__prevAdjClose[instrument]
				if shares > 0:
					partialReturn = (currAdjClose - prevAdjClose) / float(prevAdjClose)
				elif shares < 0:
					partialReturn = (currAdjClose - prevAdjClose) / float(prevAdjClose) * -1
				else:
					assert(False)

				returns += partialReturn
				count += 1
			except KeyError:
				pass

		if count > 0:
			netReturn = returns / float(count)
		else:
			netReturn = 0

		# Calculate cumulative return.
		self.__cumRet = (1 + self.__cumRet) * (1 + netReturn) - 1

		# Notify the returns
		self.onReturns(bars, netReturn, self.__cumRet)

	def onBars(self, strat, bars):
		brk = strat.getBroker()

		# Skip returns calculation on first bar.
		if self.__firstBarProcessed:
			self.__calculateReturns(bars)
		else:
			self.__firstBarProcessed = True

		# Update the shares held at the end of the bar.
		self.__shares = {}
		for instrument in brk.getActiveInstruments():
			self.__shares[instrument] = brk.getShares(instrument)

		# Update previous adjusted close values.
		for instrument in bars.getInstruments():
			self.__prevAdjClose[instrument] = bars.getBar(instrument).getAdjClose()

