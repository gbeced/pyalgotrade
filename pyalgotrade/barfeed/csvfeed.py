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
from pyalgotrade import warninghelpers
from pyalgotrade.barfeed import helpers

import csv
import datetime

# Interface for csv row parsers.
class RowParser:
	def parseBar(self, csvRowDict):
		raise Exception("Not implemented")

	def getFieldNames(self):
		raise Exception("Not implemented")

	def getDelimiter(self):
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
		if self.__toDate and bar_.getDateTime() > self.__toDate:
			return False
		if self.__fromDate and bar_.getDateTime() < self.__fromDate:
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
		self.__nextBarIdx = {}
		self.__barFilter = None
		self.__stopDispatching = False

	def start(self):
		# Set session close attributes to bars.
		for instrument, bars in self.__bars.iteritems():
			helpers.set_session_close_attributes(bars)

	def stop(self):
		pass

	def join(self):
		pass

	def setBarFilter(self, barFilter):
		self.__barFilter = barFilter

	def addBarsFromCSV(self, instrument, path, rowParser):
		self.__bars.setdefault(instrument, [])
		self.__nextBarIdx.setdefault(instrument, 0)

		# Load the csv file
		loadedBars = []
		reader = csv.DictReader(open(path, "r"), fieldnames=rowParser.getFieldNames(), delimiter=rowParser.getDelimiter())
		for row in reader:
			bar_ = rowParser.parseBar(row)
			if self.__barFilter is None or self.__barFilter.includeBar(bar_):
				loadedBars.append(bar_)

		# Add and sort the bars
		self.__bars[instrument].extend(loadedBars)
		barCmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
		self.__bars[instrument].sort(barCmp)

		self.registerInstrument(instrument)

	def stopDispatching(self):
		return self.__stopDispatching

	def fetchNextBars(self):
		# All bars must have the same datetime. We will return all the ones with the smallest datetime.
		smallestDateTime = None

		# Make a first pass to get the smallest datetime.
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars):
				if smallestDateTime == None or bars[nextIdx].getDateTime() < smallestDateTime:
					smallestDateTime = bars[nextIdx].getDateTime()

		if smallestDateTime == None:
			self.__stopDispatching = True
			return None

		# Make a second pass to get all the bars that had the smallest datetime.
		ret = {}
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars) and bars[nextIdx].getDateTime() == smallestDateTime:
				ret[instrument] = bars[nextIdx]
				self.__nextBarIdx[instrument] += 1
		return ret

######################################################################
## Yahoo CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Adj Close
#
# The csv Date column must have the following format: YYYY-MM-DD

class YahooRowParser(RowParser):
	# zone: The zone specifies the offset from Coordinated Universal Time (UTC, formerly referred to as "Greenwich Mean Time") 
	def __init__(self, zone = 0):
		self.__zone = zone

	def __parseDate(self, dateString):
		ret = datetime.datetime.strptime(dateString, "%Y-%m-%d")
		ret += datetime.timedelta(hours= (-1 * self.__zone))
		return ret

	def getFieldNames(self):
		# It is expected for the first row to have the field names.
		return None

	def getDelimiter(self):
		return ","

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
	def __init__(self, skipWarning=False):
		if not skipWarning:
			warninghelpers.deprecation_warning("pyalgotrade.barfeed.csvfeed.YahooFeed will be deprecated in the next version. Please use pyalgotrade.barfeed.yahoofeed.Feed instead.", stacklevel=2)
		BarFeed.__init__(self)
	
	def addBarsFromCSV(self, instrument, path, timeZone = 0):
		rowParser = YahooRowParser(timeZone)
		BarFeed.addBarsFromCSV(self, instrument, path, rowParser)
