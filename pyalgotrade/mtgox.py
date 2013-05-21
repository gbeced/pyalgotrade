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

from ws4py.client import WebSocketBaseClient

import json
import datetime

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Trade
class Trade:
	def __init__(self, tradeDict):
		self.__tradeDict = tradeDict

	def getAmount(self):
		"""The traded amount in item (BTC)."""
		return int(self.__tradeDict["amount_int"]) * 0.00000001

	def getDateTime(self):
		""":class:`datetime.datetime` for the trade."""
		return datetime.datetime.fromtimestamp(int(self.__tradeDict["date"]))

	def getPrice(self):
		"""Returns the price."""
		ret = int(self.__tradeDict["price_int"])
		if self.getCurrency() in ["JPY", "SEK"]:
			ret = ret * 0.001
		else:
			ret = ret * 0.00001
		return ret

	def getCurrency(self):
		"""Currency in which trade was completed."""
		return self.__tradeDict["price_currency"]

	def getType(self):
		"""Returns bid or ask, depending if this trade resulted from the execution of a bid or a ask."""
		return self.__tradeDict["trade_type"]

# https://en.bitcoin.it/wiki/MtGox/API#Number_Formats
def get_value_int(currency, value_int):
	ret = int(value_int)
	if currency in ["JPY", "SEK"]:
		ret = ret * 0.001
	elif currency == "BTC":
		ret = ret * 0.00000001
	else:
		ret = ret * 0.00001
	return ret

class Price:
	def __init__(self, priceDict):
		self.__priceDict = priceDict

	def getValue(self):
		return get_value_int(self.getCurrency(), self.__priceDict["value_int"])

	def getCurrency(self):
		return self.__priceDict["currency"]

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Ticker
class Ticker:
	def __init__(self, tickerDict):
		self.__tickerDict = tickerDict

	def getDateTime(self):
		return datetime.datetime.fromtimestamp(int(self.__tickerDict["now"]) / 1000000)

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

# https://en.bitcoin.it/wiki/MtGox/API/Streaming
class WebSocketClient(WebSocketBaseClient):
	def received_message(self, message):
		data = json.loads(message.data)
		if data["op"] == "private":
			self.onPrivate(data)
		elif data["op"] == "subscribe":
			self.onSubscribe(data)
		elif data["op"] == "unsubscribe":
			self.onUnsubscribe(data)
		elif data["op"] == "remark":
			self.onRemark(data)
		elif data["op"] == "result":
			self.onResult(data)
		else:
			self.onUnknownOperation(data["op"], data)

	def opened(self):
		pass

	def closed(self, code, reason):
		pass

	def handshake_ok(self):
		pass

	def onPrivate(self, data):
		if data["private"] == "ticker":
			self.onTicker( Ticker(data["ticker"]) )
		elif data["private"] == "trade":
			# From https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1:
			# A trade can appear in more than one currency, to ignore duplicates,
			# use only the trades having primary =Y
			if data["trade"]["primary"] == "Y":
				self.onTrade( Trade(data["trade"]) )
		elif data["private"] == "depth":
			self.onDepth(data["depth"])
		elif data["private"] == "result":
			pass

	def onSubscribe(self, data):
		pass

	def onUnsubscribe(self, data):
		pass

	def onRemark(self, data):
		pass

	def onResult(self, data):
		pass

	def onUnknownOperation(self, operation, data):
		pass

	def onTicker(self, ticker):
		pass

	def onTrade(self, trade):
		pass

	def onDepth(self, data):
		pass

