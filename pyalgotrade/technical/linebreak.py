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

from pyalgotrade import dataseries
import pyalgotrade.bar

class Line:
	"""A line in a line break chart."""

	def __init__(self, low, high, dateTime, white):
		self.__low = low
		self.__high = high
		self.__dateTime = dateTime
		self.__white = white

	def getDateTime(self):
		"""The datetime."""
		return self.__dateTime

	def getLow(self):
		"""The low value."""
		return self.__low

	def getHigh(self):
		"""The high value."""
		return self.__high

	def isWhite(self):
		"""True if the line is white (rising prices)."""
		return self.__white

	def isBlack(self):
		"""True if the line is black (falling prices)."""
		return not self.__white

class LineBreak(dataseries.DataSeries):
	"""Line Break filter as described in http://stockcharts.com/help/doku.php?id=chart_school:chart_analysis:three_line_break
	.
	This is a DataSeries of :class:`Line` instances.

	:param barDataSeries: The DataSeries instance being filtered.
	:type barDataSeries: :class:`pyalgotrade.dataseries.BarDataSeries`.
	:param reversalLines: The number of lines back to check to calculate a reversal. Must be greater than 1.
	:type reversalLines: int.
	:param useAdjustedValues: True to use adjusted high/low/close values.
	:type useAdjustedValues: boolean.
	"""

	def __init__(self, barDataSeries, reversalLines, useAdjustedValues = False):
		if not isinstance(barDataSeries, dataseries.BarDataSeries):
			raise Exception("barDataSeries must be a dataseries.BarDataSeries instance")
		if reversalLines < 2:
			raise Exception("reversalLines must be greater than 1")

		self.__barDS = barDataSeries
		self.__reversalLines = reversalLines
		self.__lines = []
		self.__dateTimes = []
		self.__nextBar = 0
		self.__useAdjustedValues = useAdjustedValues

	def __isReversal(self, value, breakUp):
		assert(len(self.__lines))
		lines = self.__lines[self.__reversalLines*-1:]
		if breakUp:
			breakPoint = max([line.getHigh() for line in lines])
			ret = value > breakPoint
		else:
			breakPoint = min([line.getLow() for line in lines])
			ret = value < breakPoint
		return ret

	def __update(self, bar):
		if len(self.__lines) > 0:
			lastLine = self.__lines[-1]
			close = pyalgotrade.bar.get_close(bar, self.__useAdjustedValues)
			if lastLine.isWhite():
				if close > lastLine.getHigh():
					# Price extends in the same direction
					line = Line(lastLine.getHigh(), close, bar.getDateTime(), True)
					self.__lines.append(line)
					self.__dateTimes.append(bar.getDateTime())
				elif self.__isReversal(close, False):
					# Price change is enough to warrant a reversal.
					line = Line(close, lastLine.getLow(), bar.getDateTime(), False)
					self.__lines.append(line)
					self.__dateTimes.append(bar.getDateTime())
			else:
				if close < lastLine.getLow():
					# Price extends in the same direction
					line = Line(close, lastLine.getLow(), bar.getDateTime(), False)
					self.__lines.append(line)
					self.__dateTimes.append(bar.getDateTime())
				elif self.__isReversal(close, True):
					# Price change is enough to warrant a reversal.
					line = Line(lastLine.getHigh(), close, bar.getDateTime(), True)
					self.__lines.append(line)
					self.__dateTimes.append(bar.getDateTime())
		else:
			white = False
			if pyalgotrade.bar.get_close(bar, self.__useAdjustedValues) >= pyalgotrade.bar.get_open(bar, self.__useAdjustedValues):
				white = True
			line = Line(pyalgotrade.bar.get_low(bar, self.__useAdjustedValues), pyalgotrade.bar.get_high(bar, self.__useAdjustedValues), bar.getDateTime(), white)
			self.__lines.append(line)
			self.__dateTimes.append(bar.getDateTime())

	def __checkUpdate(self):
		barDsLength = len(self.__barDS)
		if barDsLength > self.__nextBar:
			for i in xrange(self.__nextBar, barDsLength):
				self.__update(self.__barDS[i])
			self.__nextBar = barDsLength

	def getFirstValidPos(self):
		return 0

	def getLength(self):
		self.__checkUpdate()
		return len(self.__lines)

	def getValueAbsolute(self, pos):
		self.__checkUpdate()
		ret = None
		if pos >= 0 and pos < len(self.__lines):
			ret = self.__lines[pos]
		return ret

	def getDateTimes(self):
		self.__checkUpdate()
		return self.__dateTimes

