# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""

from pyalgotrade.barfeed import csvfeed, BarFeed
from pyalgotrade.providers.interactivebrokers import ibbar

import datetime
import copy 
import Queue


######################################################################
## Interactive Brokers CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Trade Count,WAP,Has Gaps
#
# The csv Date column must have the following format: YYYYMMDD	hh:mm:ss


class RowParser(csvfeed.RowParser):
	def __init__(self, instrument, zone = 0):
		self.__zone = zone
		self.__instrument = instrument

	def __parseDate(self, dateString):
		ret = datetime.datetime.strptime(dateString, "%Y-%m-%d %H:%M:%S")
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
		volume = int(csvRowDict["Volume"])
		tradeCnt = int(csvRowDict["TradeCount"])
		VWAP = float(csvRowDict["VWAP"])
		# hasGaps = bool(csvRowDict["HasGaps"] == "True")

		return ibbar.Bar(self.__instrument, date, open_, high, low, close, volume, VWAP, tradeCnt)

class CSVFeed(csvfeed.BarFeed):
	"""A :class:`pyalgotrade.barfeed.BarFeed` that loads bars from a CSV file downloaded from IB TWS"""
	def __init__(self):
		csvfeed.BarFeed.__init__(self)
	
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
		rowParser = RowParser(instrument, timeZone)
		csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser)


class LiveFeed(BarFeed):
		def __init__(self, ibConnection, timezone=0):
				BarFeed.__init__(self)

				# The zone specifies the offset from Coordinated Universal Time (UTC, 
				# formerly referred to as "Greenwich Mean Time") 
				self.__zone = timezone

				# Connection to the IB's TWS
				self.__ibConnection = ibConnection

				self.__currentDateTime = None
				self.__currentBars = {}
				self.__queue = Queue.Queue()

				self.__running = True


		def start(self):
			pass

		def stop(self):
			self.__running = False

		def join(self):
			pass

		def fetchNextBars(self):
				timeout = 10 # Seconds

				while self.__running:
					try:
						ret = self.__queue.get(True, timeout)
						if len(ret) == 0:
								ret = None
						return ret
					except Queue.Empty:
						pass
				else:
					return None

		def subscribeRealtimeBars(self, instrument, useRTH_=0):
				self.__ibConnection.subscribeRealtimeBars(instrument, self.onRealtimeBars, useRTH=useRTH_)

				# Register the instrument
				self.registerInstrument(instrument)
		
		def unsubscribeRealtimeBars(self, instrument):
				self.__ibConnection.unsubscribeRealtimeBars(instrument)

				# TODO: Deregister instrument

		def onRealtimeBars(self, bar):
				if len(self.__currentBars) == 0:
						self.__currentDatetime = bar.getDateTime()
						self.__currentBars[bar.getInstrument()] = bar
				elif len(self.__currentBars) > 0:
						if self.__currentDatetime != bar.getDateTime():
								bars = copy.copy(self.__currentBars)
								self.__currentDatetime = bar.getDateTime()
								#self.__currentBars[bar.getInstrument()] = bar # First bar in the next set of bars.
								self.__currentBars = {bar.getInstrument() : bar} # First bar in the next set of bars.
								self.__queue.put(bars)
						else:
								self.__currentBars[bar.getInstrument()] = bar

# vim: noet:ci:pi:sts=0:sw=4:ts=4
