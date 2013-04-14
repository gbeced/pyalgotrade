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
from pyalgotrade.utils import dt
from pyalgotrade.barfeed import membf

import csv
import datetime
import types
import pytz

# A faster (but limited) version of csv.DictReader
class FastDictReader:
	def __init__(self, f, fieldnames=None, dialect="excel", *args, **kwds):
		self.__fieldNames = fieldnames
		self.reader = csv.reader(f, dialect, *args, **kwds)
		if self.__fieldNames is None:
			self.__fieldNames = self.reader.next()
		self.__dict = {}

	def __iter__(self):
		return self

	def next(self):
		# Skip empty rows.
		row = self.reader.next()
		while row == []:
			row = self.reader.next()

		# Check that the row has the right number of columns.
		assert(len(self.__fieldNames) == len(row))

		# Copy the row values into the dict.
		for i in xrange(len(self.__fieldNames)):
			self.__dict[self.__fieldNames[i]] = row[i]

		return self.__dict

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
	timezone = pytz.timezone("US/Eastern")

	def __init__(self, fromDate = None, toDate = None):
		DateRangeFilter.__init__(self, fromDate, toDate)

		self.__fromTime = datetime.time(9, 30, 0)
		self.__toTime = datetime.time(16, 0, 0)

	def includeBar(self, bar_):
		ret = DateRangeFilter.includeBar(self, bar_)
		if ret:
			# Check day of week
			barDay = bar_.getDateTime().weekday()
			if barDay > 4:
				return False

			# Check time
			barTime = dt.localize(bar_.getDateTime(), USEquitiesRTH.timezone).time()
			if barTime < self.__fromTime:
				return False
			if barTime > self.__toTime:
				return False
		return ret

class BarFeed(membf.Feed):
	"""A CSV file based :class:`pyalgotrade.barfeed.BarFeed`.

	.. note::
		This is a base class and should not be used directly.
	"""

	def __init__(self, frequency):
		membf.Feed.__init__(self, frequency)
		self.__barFilter = None
		self.__dailyTime = datetime.time(23, 59, 59)

	def getDailyBarTime(self):
		"""Returns the time to set to daily bars when that information is not present in CSV files. Defaults to 23:59:59.

		:rtype: datetime.time.
		"""

		return self.__dailyTime

	def setDailyBarTime(self, time):
		"""Sets the time to set to daily bars when that information is not present in CSV files.

		:param time: The time to set.
		:type time: datetime.time.
		"""

		self.__dailyTime = time

	def setBarFilter(self, barFilter):
		self.__barFilter = barFilter

	def addBarsFromCSV(self, instrument, path, rowParser):
		# Load the csv file
		loadedBars = []
		reader = FastDictReader(open(path, "r"), fieldnames=rowParser.getFieldNames(), delimiter=rowParser.getDelimiter())
		for row in reader:
			bar_ = rowParser.parseBar(row)
			if bar_ != None and (self.__barFilter is None or self.__barFilter.includeBar(bar_)):
				loadedBars.append(bar_)

		self.addBarsFromSequence(instrument, loadedBars)

######################################################################
## Yahoo CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Adj Close
#
# The csv Date column must have the following format: YYYY-MM-DD

def parse_date(date):
	# Sample: 2005-12-30
	# This custom parsing works faster than:
	# datetime.datetime.strptime(date, "%Y-%m-%d")
	year = int(date[0:4])
	month = int(date[5:7])
	day = int(date[8:10])
	ret = datetime.datetime(year, month, day)
	return ret

class YahooRowParser(RowParser):
	def __init__(self, dailyBarTime, timezone = None):
		self.__dailyBarTime = dailyBarTime
		self.__timezone = timezone

	def __parseDate(self, dateString):
		ret = parse_date(dateString)
		# Time on Yahoo! Finance CSV files is empty. If told to set one, do it.
		if self.__dailyBarTime != None:
			ret = datetime.datetime.combine(ret, self.__dailyBarTime)
		# Localize the datetime if a timezone was given.
		if self.__timezone:
			ret = dt.localize(ret, self.__timezone)
		return ret

	def getFieldNames(self):
		# It is expected for the first row to have the field names.
		return None

	def getDelimiter(self):
		return ","

	def parseBar(self, csvRowDict):
		dateTime = self.__parseDate(csvRowDict["Date"])
		close = float(csvRowDict["Close"])
		open_ = float(csvRowDict["Open"])
		high = float(csvRowDict["High"])
		low = float(csvRowDict["Low"])
		volume = float(csvRowDict["Volume"])
		adjClose = float(csvRowDict["Adj Close"])
		return bar.Bar(dateTime, open_, high, low, close, volume, adjClose)

class YahooFeed(BarFeed):
	def __init__(self, timezone = None, skipWarning=False):
		if type(timezone) == types.IntType:
			raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

		if not skipWarning:
			warninghelpers.deprecation_warning("pyalgotrade.barfeed.csvfeed.YahooFeed will be deprecated in the next version. Please use pyalgotrade.barfeed.yahoofeed.Feed instead.", stacklevel=2)

		BarFeed.__init__(self, barfeed.Frequency.DAY)
		self.__timezone = timezone
	
	def addBarsFromCSV(self, instrument, path, timezone = None):
		if type(timezone) == types.IntType:
			raise Exception("timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

		if timezone is None:
			timezone = self.__timezone
		rowParser = YahooRowParser(self.getDailyBarTime(), timezone)
		BarFeed.addBarsFromCSV(self, instrument, path, rowParser)
