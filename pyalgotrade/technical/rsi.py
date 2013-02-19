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

# RSI = 100 - 100 / (1 + RS)
# RS = Average gain / Average loss
# First Average Gain = Sum of Gains over the past 14 periods / 14
# First Average Loss = Sum of Losses over the past 14 periods / 14
# Average Gain = [(previous Average Gain) x 13 + current Gain] / 14
# Average Loss = [(previous Average Loss) x 13 + current Loss] / 14
#
# RSI is 0 when the Average Gain equals zero. Assuming a 14-period RSI, a zero RSI value means prices moved lower all
# 14 periods. There were no gains to measure.
# RSI is 100 when the Average Loss equals zero. This means prices moved higher all 14 periods.
# There were no losses to measure.
#
# If Average Loss equals zero, a "divide by zero" situation occurs for RS and RSI is set to 100 by definition.
# Similarly, RSI equals 0 when Average Gain equals zero.
#
# RSI is considered overbought when above 70 and oversold when below 30.
# These traditional levels can also be adjusted to better fit the security or analytical requirements.
# Raising overbought to 80 or lowering oversold to 20 will reduce the number of overbought/oversold readings.
# Short-term traders sometimes use 2-period RSI to look for overbought readings above 80 and oversold readings below 20.

def gain_loss_one(prevValue, nextValue):
	change = nextValue - prevValue  
	if change < 0:
		gain = 0
		loss = abs(change)
	else:
		gain = change
		loss = 0
	return gain, loss

def avg_gain_loss(values):
	assert(len(values) > 1)

	gain = 0
	loss = 0
	for i in xrange(1, len(values)):
		currGain, currLoss = gain_loss_one(values[i-1], values[i])
		gain += currGain
		loss += currLoss
	return (gain/float(len(values)-1), loss/float(len(values)-1))

class RSI(technical.DataSeriesFilter):
	"""Relative Strength Index filter as described in http://stockcharts.com/school/doku.php?id=chart_school:technical_indicators:relative_strength_index_rsi.

	:param dataSeries: The DataSeries instance being filtered.
	:type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
	:param period: The period. Note that if period is **n**, then **n+1** values are used. Must be > 1.
	:type period: int.
	"""

	def __init__(self, dataSeries, period):
		assert(period > 1)
		# We need N + 1 samples to calculate N averages because they are calculated based on the diff with previous values.
		technical.DataSeriesFilter.__init__(self, dataSeries, period + 1)

		self.__period = period
		self.__averages = {}

	def getPeriod(self):
		return self.__period

	def __getAverages(self, pos):
		ret =  self.__averages.get(pos, None)
		if ret is None:
			if pos == self.getFirstValidPos():
				# First averages
				values = self.getDataSeries().getValuesAbsolute(pos - self.__period, pos)
				assert(values is not None)
				ret = avg_gain_loss(values)
			else:
				# Rest of averages are smoothed
				prevAvgGain, prevAvgLoss = self.__getAverages(pos - 1)
				assert(prevAvgGain != None)
				assert(prevAvgLoss != None)

				prevValue = self.getDataSeries().getValueAbsolute(pos-1)
				assert(prevValue != None)
				currValue = self.getDataSeries().getValueAbsolute(pos)
				assert(currValue != None)
				currGain, currLoss = gain_loss_one(prevValue, currValue)

				avgGain = (prevAvgGain * (self.__period-1) + currGain) / float(self.__period)
				avgLoss = (prevAvgLoss * (self.__period-1) + currLoss) / float(self.__period)
				ret = (avgGain, avgLoss)

			self.__averages[pos] = ret

		return ret

	def calculateValue(self, firstPos, lastPos):
		avgGain, avgLoss = self.__getAverages(lastPos)

		if avgLoss == 0:
			return 100
		rs = avgGain / avgLoss
		rsi = 100 - 100 / (1 + rs)

		return rsi

