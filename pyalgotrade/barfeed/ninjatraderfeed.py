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

from pyalgotrade.barfeed import csvfeed
from pyalgotrade import bar

import datetime

######################################################################
## NinjaTrader CSV parser
# Each bar must be on its own line and fields must be separated by semicolon (;).
#
# Minute Bars Format:
# yyyyMMdd HHmmss;open price;high price;low price;close price;volume
#
# Daily Bars Format:
# yyyyMMdd;open price;high price;low price;close price;volume

class Frequency:
	MINUTE = 1
	DAILY = 2

class RowParser(csvfeed.RowParser):
	# zone: The zone specifies the offset from Coordinated Universal Time (UTC, formerly referred to as "Greenwich Mean Time") 
	def __init__(self, frequency, zone = 0):
		self.__frequency = frequency
		self.__zone = zone

	def __parseDateTime(self, dateTime):
		ret = None
		if self.__frequency == Frequency.MINUTE:
			ret = datetime.datetime.strptime(dateTime, "%Y%m%d %H%M%S")
			ret += datetime.timedelta(hours= (-1 * self.__zone))
		elif self.__frequency == Frequency.DAILY:
			ret = datetime.datetime.strptime(dateTime, "%Y%m%d")
		else:
			assert(False)
		return ret

	def getFieldNames(self):
		return ["Date Time", "Open", "High", "Low", "Close", "Volume"]

	def getDelimiter(self):
		return ";"

	def parseBar(self, csvRowDict):
		dateTime = self.__parseDateTime(csvRowDict["Date Time"])
		close = float(csvRowDict["Close"])
		open_ = float(csvRowDict["Open"])
		high = float(csvRowDict["High"])
		low = float(csvRowDict["Low"])
		volume = float(csvRowDict["Volume"])
		return bar.Bar(dateTime, open_, high, low, close, volume, None)

class Feed(csvfeed.BarFeed):
	"""A :class:`pyalgotrade.barfeed.BarFeed` that loads bars from a CSV file exported from NinjaTrader.

	:param frequency: The frequency of the bars.

	.. note::

		Valid **frequency** parameter values are:

		 * ninjatraderfeed.Frequency.MINUTE 
		 * ninjatraderfeed.Frequency.DAILY
	"""

	def __init__(self, frequency):
		csvfeed.BarFeed.__init__(self)
		self.__frequency = frequency

	def addBarsFromCSV(self, instrument, path, timeZone = 0):
		"""Loads bars for a given instrument from a CSV formatted file.
		The instrument gets registered in the bar feed.
		
		:param instrument: Instrument identifier.
		:type instrument: string.
		:param path: The path to the file.
		:type path: string.
		:param timeZone: The timezone for bars. 0 if bar dates are in UTC.
		:type timeZone: int.
		"""

		rowParser = RowParser(self.__frequency, timeZone)
		csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser)

