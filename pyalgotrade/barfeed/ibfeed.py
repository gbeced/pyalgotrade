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
.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""

from pyalgotrade.barfeed import csvfeed, BarFeed
from pyalgotrade import bar

import datetime
import threading, copy 
from time import sleep


######################################################################
## Interactive Brokers CSV parser
# Each bar must be on its own line and fields must be separated by comma (,).
#
# Bars Format:
# Date,Open,High,Low,Close,Volume,Trade Count,WAP,Has Gaps
#
# The csv Date column must have the following format: YYYYMMDD  hh:mm:ss


class IBRowParser(csvfeed.RowParser):
	def __init__(self, zone = 0):
		self.__zone = zone

	def __parseDate(self, dateString):
		ret = datetime.datetime.strptime(dateString, "%Y%m%d  %H:%M:%S")
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
                # TODO: Add these variables to Bar
		# tradeCnt = int(csvRowDict["TradeCount"])
		# WAP = float(csvRowDict["WAP"])
		# hasGaps = bool(csvRowDict["HasGaps"] == "True")

		return bar.Bar(date, open_, high, low, close, volume, None)

class IBCSVFeed(csvfeed.BarFeed):
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
		rowParser = IBRowParser(timeZone)
		csvfeed.BarFeed.addBarsFromCSV(self, instrument, path, rowParser)


class IBLiveFeed(BarFeed):
        def __init__(self, ibConnection, timezone=0, twsHost='localhost', twsPort=7496, twsClientId=27):
                BarFeed.__init__(self)

                # The zone specifies the offset from Coordinated Universal Time (UTC, 
                # formerly referred to as "Greenwich Mean Time") 
                self.__zone = timezone

                # Connection to the IB's TWS
                self.__ibConnection = ibConnection

                # Buffer for the bars with lock. Each item in a list is a IBBar
                # returned from the ibConnections realtime feed.
                # Locking is necessary as the ibConnection runs on a separate thread. 
                self.__bars = {}
                self.__barsLock = threading.Condition()


        def subscribeRealtimeBars(self, instrument, useRTH_=0):
                self.__ibConnection.subscribeRealtimeBars(instrument, self.onRealtimeBars, useRTH=useRTH_)

                # Register the instrument
                self.registerInstrument(instrument)
        
        def unsubscribeRealtimeBars(self, instrument):
                self.__ibConnection.unsubscribeRealtimeBars(instrument)

                # TODO: Deregister instrument

        def onRealtimeBars(self, bar):
                instrument = bar.getInstrument()

                self.__barsLock.acquire()
                self.__bars[instrument] = bar
                self.__barsLock.notify()
                self.__barsLock.release()

        def fetchNextBars(self):
                # Acquire the lock and wait until data is available
                self.__barsLock.acquire()
                self.__barsLock.wait()

                # Make shallow copy of the buffer
                # This variable will be returned, the
                # buffer will be cleared
                barsDict = copy.copy(self.__bars)

                # Clear the bar buffer
                self.__bars.clear()

                # Release the lock
                self.__barsLock.release()

                if len(barsDict) == 0:
                    # Signal the end of the stream 
                    # by returning None
                    return None
                else:
                    # Return the new bars
                    return barsDict

