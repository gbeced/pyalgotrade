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

from pyalgotrade import bar
from pyalgotrade import barfeed

import csv
import datetime

# Interface for csv row parsers.
class RowParser:
	def parseBar(self, csvRowDict):
		raise Exception("Not implemented")

# Interface for bar filters.
class BarFilter:
	def includeBar(self, bar_):
		raise Exception("Not implemented")

class DateRangeFilter(BarFilter):
	def __init__(self, fromDate = None, toDate = None):
		self.__fromDate = fromDate
		self.__toDate = toDate

	def includeBar(self, bar_):
		if self.__toDate and bar_.getDateTime().date() > self.__toDate:
			return False
		if self.__fromDate and bar_.getDateTime().date() < self.__fromDate:
			return False
		return True

# US Equities Regular Trading Hours filter
# Monday ~ Friday
# 9:30 ~ 16 (GMT-5)
class USEquitiesRTH(DateRangeFilter):
	zone = -5
	def __init__(self, fromDate = None, toDate = None):
		DateRangeFilter.__init__(self, fromDate, toDate)
		# Assuming that datetimes are in UTC
		self.__fromTime = datetime.time(9 + (USEquitiesRTH.zone * -1), 30, 0)
		self.__toTime = datetime.time(16 + (USEquitiesRTH.zone * -1), 0, 0)

	def includeBar(self, bar_):
		ret = DateRangeFilter.includeBar(self, bar_)
		if ret:
			# Check day of week
			barDay = bar_.getDateTime().weekday()
			if barDay > 4:
				return False

			# Check time
			barTime = bar_.getDateTime().time()
			if barTime < self.__fromTime:
				return False
			if barTime > self.__toTime:
				return False
		return ret

class BarFeed(barfeed.BarFeed):
	def __init__(self):
		barfeed.BarFeed.__init__(self)
		self.__bars = {}
		self.currentBar = 0
		self.__barFilter = None

	def setBarFilter(self, barFilter):
		self.__barFilter = barFilter

	def addBarsFromCSV(self, instrument, path, rowParser):
		assert(self.currentBar == 0)

		self.__bars.setdefault(instrument, [])

		# Load the csv file
		loadedBars = []
		reader = csv.DictReader(open(path, "r"))
		for row in reader:
			bar_ = rowParser.parseBar(row)
			if self.__barFilter is None or self.__barFilter.includeBar(bar_):
				loadedBars.append(bar_)

		# Add and sort the bars
		self.__bars[instrument].extend(loadedBars)
		barCmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
		self.__bars[instrument].sort(barCmp)

		self.registerInstrument(instrument)

	def fetchNextBars(self):
		ret = {}
		for instrument, bars in self.__bars.iteritems():
			if self.currentBar >= len(bars):
				return None
			ret[instrument] = bars[self.currentBar]
		self.currentBar += 1
		return ret

######################################################################
## Yahoo CSV parser
# The csv Date column must have the following format: YYYY-MM-DD

class YahooRowParser(RowParser):
	# zone: The zone specifies the offset from Coordinated Universal Time (UTC, formerly referred to as "Greenwich Mean Time") 
	def __init__(self, zone = 0):
		self.__zone = zone

	def __parseDate(self, dateString):
		ret = datetime.datetime.strptime(dateString, "%Y-%m-%d")
		ret += datetime.timedelta(hours= (-1 * self.__zone))
		return ret

	def parseBar(self, csvRowDict):
		date = self.__parseDate(csvRowDict["Date"])
		close = float(csvRowDict["Close"])
		open_ = float(csvRowDict["Open"])
		high = float(csvRowDict["High"])
		low = float(csvRowDict["Low"])
		volume = float(csvRowDict["Volume"])
		adjClose = float(csvRowDict["Adj Close"])
		return bar.Bar(date, open_, high, low, close, volume, adjClose)

class YahooFeed(BarFeed):
	"""A :class:`pyalgotrade.barfeed.BarFeed` that loads bars from a CSV file downloaded from Yahoo! Finance."""
	def __init__(self):
		BarFeed.__init__(self)
	
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
		rowParser = YahooRowParser(timeZone)
		BarFeed.addBarsFromCSV(self, instrument, path, rowParser)

######################################################################
## Interactive Brokers intraday CSV parser
# The csv 'Date Time' column must have the following format: YYYYMMDD HHMMSS

class IBIntraDayRowParser(RowParser):
	# zone: The zone specifies the offset from Coordinated Universal Time (UTC, formerly referred to as "Greenwich Mean Time") 
	def __init__(self, zone = 0):
		self.__zone = zone

	def __parseDateTime(self, dateTime):
		ret = datetime.datetime.strptime(dateTime, "%Y%m%d %H%M%S")
		ret += datetime.timedelta(hours= (-1 * self.__zone))
		return ret

	def parseBar(self, csvRowDict):
		dateTime = self.__parseDateTime(csvRowDict["Date Time"])
		close = float(csvRowDict["Close"])
		open_ = float(csvRowDict["Open"])
		high = float(csvRowDict["High"])
		low = float(csvRowDict["Low"])
		volume = float(csvRowDict["Volume"])
		return bar.Bar(dateTime, open_, high, low, close, volume, None)

