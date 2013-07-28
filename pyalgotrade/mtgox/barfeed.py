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

from pyalgotrade import barfeed
from pyalgotrade import bar
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import dataseries
from pyalgotrade.utils import dt
from pyalgotrade.mtgox import base

class TradeBar(bar.Bar):
	# Optimization to reduce memory footprint.
	__slots__ = ('__dateTime', '__price', '__amount', '__tradeType', '__sessionClose', '__barsTillSessionClose')

	def __init__(self, dateTime, price, amount, tradeType):
		self.__dateTime = dateTime
		self.__price = price
		self.__amount = amount
		self.__tradeType = tradeType 
		self.__sessionClose = False
		self.__barsTillSessionClose = None

	def __setstate__(self, state):
		(self.__dateTime, self.__price, self.__amount, self.__amount, self.__sessionClose, self.__barsTillSessionClose) = state

	def __getstate__(self):
		return (self.__dateTime, self.__price, self.__amount, self.__amount, self.__sessionClose, self.__barsTillSessionClose)

	def getDateTime(self):
		return self.__dateTime

	def getOpen(self):
		return self.__price

	def getHigh(self):
		return self.__price

	def getLow(self):
		return self.__price

	def getClose(self):
		return self.__price

	def getVolume(self):
		return self.__amount

	def getTradeType(self):
		return self.__tradeType

	def getAdjOpen(self):
		return self.__price

	def getAdjHigh(self):
		return self.__price

	def getAdjLow(self):
		return self.__price

	def getAdjClose(self):
		return self.__price

	def getTypicalPrice(self):
		return self.__price

	def getSessionClose(self):
		# Returns True if this is the last bar for the session, or False otherwise.
		return self.__sessionClose

	def setSessionClose(self, sessionClose):
		self.__sessionClose = sessionClose
		if sessionClose:
			self.__barsTillSessionClose = 0

	def getBarsTillSessionClose(self):
		return self.__barsTillSessionClose

	def setBarsTillSessionClose(self, barsTillSessionClose):
		self.__barsTillSessionClose = barsTillSessionClose

class RowParser(csvfeed.RowParser):
	def __init__(self, timezone = None):
		self.__timezone = timezone

	def getFieldNames(self):
		# It is expected for the first row to have the field names.
		return None

	def getDelimiter(self):
		return ","

	def parseBar(self, csvRowDict):
		tid = int(csvRowDict["id"])
		price = float(csvRowDict["price"])
		amount = float(csvRowDict["amount"])
		tradeType = csvRowDict["type"]

		dateTime = base.tid_to_datetime(tid)
		# Localize the datetime if a timezone was given.
		if self.__timezone:
			dateTime = dt.localize(dateTime, self.__timezone)

		return TradeBar(dateTime, price, amount, tradeType)

class CSVTradeFeed(csvfeed.BarFeed):
	"""A BarFeed that builds bars from a trades CSV file.

	:param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
	:type timezone: A pytz timezone.
	:param frequency: Reserved for future use. Currently ignored.
	:param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
		If not None, it must be greater than 0.
		Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
	:type maxLen: int.

	.. note::
		Note that a :class:`pyalgotrade.bar.Bar` instance will be created for every trade, so
		open, high, low and close values will all be the same.
	"""

	def __init__(self, timezone = None, frequency=None, maxLen=dataseries.DEFAULT_MAX_LEN):
		csvfeed.BarFeed.__init__(self, barfeed.Frequency.TRADE, maxLen)
		self.__timezone = timezone
	
	def addBarsFromCSV(self, path, timezone = None):
		"""Loads bars from a trades CSV formatted file.

		:param path: The path to the file.
		:type path: string.
		:param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
		:type timezone: A pytz timezone.

		.. note::
			Every file that you load bars from must have trades in the same currency.
		"""

		if timezone is None:
			timezone = self.__timezone
		rowParser = RowParser(timezone)
		csvfeed.BarFeed.addBarsFromCSV(self, "BTC", path, rowParser)

class LiveTradeFeed(barfeed.BarFeed):
	"""A real-time BarFeed that builds bars from live trades.

	:param client: A MtGox client.
	:type client: :class:`pyalgotrade.mtgox.client.Client`.
	:param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
		If not None, it must be greater than 0.
		Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
	:type maxLen: int.

	.. note::
		Note that a :class:`pyalgotrade.bar.Bar` instance will be created for every trade, so
		open, high, low and close values will all be the same.
	"""

	def __init__(self, client, maxLen=dataseries.DEFAULT_MAX_LEN):
		barfeed.BarFeed.__init__(self, barfeed.Frequency.TRADE, maxLen)
		self.__barDicts = []
		self.__currency = client.getCurrency()
		self.registerInstrument("BTC")
		client.getTradeEvent().subscribe(self.__onTrade)
		# Dispatch after the client.
		self.__dipatchPriority = client.getDispatchPriority() + 1

	def getDispatchPriority(self):
		return self.__dipatchPriority

	def isRealTime(self):
		return True

	def __onTrade(self, trade):
		if trade.getCurrency() == self.__currency:
			# Build a bar for each trade.
			# We're using getDateTimeWithMicroseconds instead of getDateTime because sometimes
			# there are many trades in the same second and that produces errors in:
			# - barfeed.BarFeed.getNextBars and in 
			# - dataseries.SequenceDataSeries.appendWithDateTime
			barDict = {
					"BTC" : TradeBar(trade.getDateTimeWithMicroseconds(), trade.getPrice(), trade.getAmount(), trade.getType())
					}
			self.__barDicts.append(barDict)

			# Dispatch immediately
			self.dispatch()

	def fetchNextBars(self):
		ret = None
		if len(self.__barDicts):
			ret = self.__barDicts.pop(0)
		return ret

	def peekDateTime(self):
		# Return None since this is a realtime subject.
		return None

	def eof(self):
		return len(self.__barDicts) == 0

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

