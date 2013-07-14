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

import datetime

from pyalgotrade.utils import dt

def timestamp_to_tid(unixTime):
	return unixTime * 1000000

def tid_to_datetime(tid):
	unixTime = int(tid) / 1000000.0
	return dt.timestamp_to_datetime(unixTime)

def datetime_to_tid(dateTime):
	unixTime = dt.datetime_to_timestamp(dt.as_utc(dateTime))
	return timestamp_to_tid(unixTime)

# https://en.bitcoin.it/wiki/MtGox/API#Number_Formats
def from_value_int(currency, value_int):
	ret = int(value_int)
	if currency in ["JPY", "SEK"]:
		ret = ret * 0.001
	elif currency == "BTC":
		ret = ret * 0.00000001
	else:
		ret = ret * 0.00001
	return ret

def to_value_int(currency, value):
	if currency in ["JPY", "SEK"]:
		ret = value / 0.001
	elif currency == "BTC":
		ret = value / 0.00000001
	else:
		ret = value / 0.00001
	return ret

def to_amount_int(value):
	return value / 0.00000001

def from_amount_int(value_int):
	return int(value_int) * 0.00000001

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Trade
class Trade:
	def __init__(self, tradeDict):
		self.__tradeDict = tradeDict

	def getAmount(self):
		"""The traded amount in item (BTC)."""
		return from_amount_int(self.__tradeDict["amount_int"])

	def getDateTime(self):
		""":class:`datetime.datetime` for the trade."""
		return datetime.datetime.fromtimestamp(int(self.__tradeDict["date"]))

	def getDateTimeWithMicroseconds(self):
		""":class:`datetime.datetime` for the trade."""
		return datetime.datetime.fromtimestamp(int(self.__tradeDict["tid"]) / 1000000.0)

	def getPrice(self):
		"""Returns the price."""
		return from_value_int(self.getCurrency(), self.__tradeDict["price_int"])

	def getCurrency(self):
		"""Currency in which trade was completed."""
		return self.__tradeDict["price_currency"]

	def getType(self):
		"""Returns bid or ask, depending if this trade resulted from the execution of a bid or a ask."""
		return self.__tradeDict["trade_type"]

class Price:
	def __init__(self, priceDict):
		self.__priceDict = priceDict

	def getValue(self):
		return from_value_int(self.getCurrency(), self.__priceDict["value_int"])

	def getCurrency(self):
		return self.__priceDict["currency"]

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Ticker
class Ticker:
	def __init__(self, tickerDict):
		self.__tickerDict = tickerDict

	def getDateTime(self):
		return datetime.datetime.fromtimestamp(int(self.__tickerDict["now"]) / 1000000.0)

	def getAverage(self):
		return Price(self.__tickerDict["avg"])

	def getBuy(self):
		return Price(self.__tickerDict["buy"])

	def getHigh(self):
		return Price(self.__tickerDict["high"])

	def getLast(self):
		return Price(self.__tickerDict["last"])

	def getLastLocal(self):
		return Price(self.__tickerDict["last_local"])

	def getLastOrig(self):
		return Price(self.__tickerDict["last_orig"])

	def getLow(self):
		return Price(self.__tickerDict["low"])

	def getSell(self):
		return Price(self.__tickerDict["sell"])

	def getVolume(self):
		return Price(self.__tickerDict["vol"])

	def getVWAP(self):
		return Price(self.__tickerDict["vwap"])

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Depth
class Depth:
	def __init__(self, depthDict):
		self.__depthDict = depthDict

	def getCurrency(self):
		"""The currency affected."""
		return self.__depthDict["currency"]

	def getDateTime(self):
		return datetime.datetime.fromtimestamp(int(self.__depthDict["now"]) / 1000000.0)

	def getPrice(self):
		"""Returns the price at which volume change happened."""
		return from_value_int(self.getCurrency(), self.__depthDict["price_int"])

	def getTotalVolume(self):
		"""Total volume at this price, after applying the depth update, can be used as a starting point before applying subsequent updates.."""
		return from_value_int("BTC", self.__depthDict["total_volume_int"])

	def getType(self):
		"""Type of order at this depth, either 'ask' or 'bid'."""
		return self.__depthDict["type_str"]

	def getVolume(self):
		"""Volume change."""
		return from_value_int("BTC", self.__depthDict["volume_int"])

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#user_order
class UserOrder:
	class Status:
		PENDING = "pending"
		POST_PENDING = "post-pending"
		OPEN = "open"
		EXECUTING = "executing"
		INVALID = "invalid"
		STOP = "stop"

	def __init__(self, userOrderDict):
		self.__userOrderDict = userOrderDict

	def getDict(self):
		return self.__userOrderDict

	def getId(self):
		"""Returns the order GUID."""
		return self.__userOrderDict["oid"]

	def getCurrency(self):
		"""The currency."""
		return self.__userOrderDict["currency"]

	def isCanceled(self):
		"""Returns True if the order was canceled."""
		return len(self.__userOrderDict) == 1 and "oid" in self.__userOrderDict

	def getAmount(self):
		"""The traded amount in item (BTC)."""
		return Price(self.__userOrderDict["amount"]).getValue()

	def isMarketOrder(self):
		"""Returns True if this is a market order."""
		return "price" not in self.__userOrderDict

	def getPrice(self):
		"""The price. This will fail for market orders."""
		return Price(self.__userOrderDict["price"]).getValue()

	def getType(self):
		"""Type of order, either 'ask' or 'bid'."""
		return self.__userOrderDict["type"]

	def getStatus(self):
		"""The order status."""
		return self.__userOrderDict["status"]

	def getDateTime(self):
		""":class:`datetime.datetime` for the order."""
		return datetime.datetime.fromtimestamp(int(self.__userOrderDict["date"]))

