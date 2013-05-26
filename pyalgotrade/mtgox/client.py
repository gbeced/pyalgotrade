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
from pyalgotrade import observer
import pyalgotrade.logger

import json
import datetime
import threading
import Queue

logger = pyalgotrade.logger.getLogger("mtgox")

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
		return get_value_int(self.getCurrency(), self.__tradeDict["price_int"])

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

# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Depth
class Depth:
	def __init__(self, depthDict):
		self.__depthDict = depthDict

	def getCurrency(self):
		"""The currency affected."""
		return self.__depthDict["currency"]

	def getDateTime(self):
		return datetime.datetime.fromtimestamp(int(self.__depthDict["now"]) / 1000000)

	def getPrice(self):
		"""Returns the price at which volume change happened."""
		return get_value_int(self.getCurrency(), self.__depthDict["price_int"])

	def getTotalVolume(self):
		"""Total volume at this price, after applying the depth update, can be used as a starting point before applying subsequent updates.."""
		return get_value_int("BTC", self.__depthDict["total_volume_int"])

	def getType(self):
		"""type of order at this depth, either 'ask' or 'bid'."""
		return self.__depthDict["type_str"]

	def getVolume(self):
		"""Volume change."""
		return get_value_int("BTC", self.__depthDict["volume_int"])

# https://en.bitcoin.it/wiki/MtGox/API/Streaming
class WebSocketClient(WebSocketBaseClient):
	def __init__(self, currencies, ticker=True, trade=True, depth=True):
		# Using this URL will receive all messages.
		# url = 'ws://websocket.mtgox.com/mtgox'
		url = 'ws://websocket.mtgox.com/'
		WebSocketBaseClient.__init__(self, url)
		self.__currencies = currencies
		self.__ticker = ticker
		self.__trade = trade
		self.__depth = depth

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

	def subscribe(self, channel):
		msg = '{"channel":"%s", "op":"mtgox.subscribe"}' % channel
		self.send(msg, False)

	def opened(self):
		if self.__trade:
			self.subscribe("trade.BTC")

		for currency in self.__currencies:
			if self.__ticker:
				channel = "ticker.BTC%s" % currency
				self.subscribe(channel)
			if self.__depth:
				channel = "depth.BTC%s" % currency
				self.subscribe(channel)

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
			self.onDepth( Depth(data["depth"]) )
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

	def onDepth(self, depth):
		pass

class WS2Client(WebSocketClient):
	QUEUE_ELEMENT_TICKER = 1
	QUEUE_ELEMENT_TRADE = 2

	def __init__(self, currencies, queue):
		WebSocketClient.__init__(self, currencies, ticker=True, trade=True, depth=False)
		self.__queue = queue

	def closed(self, code, reason):
		logger.info("Closed. Code: %s. Reason: %s." % (code, reason))

	def onRemark(self, data):
		logger.info("Remark: %s." % (data["message"]))

	def onTicker(self, ticker):
		self.__queue.put((WS2Client.QUEUE_ELEMENT_TICKER, ticker))

	def onTrade(self, trade):
		self.__queue.put((WS2Client.QUEUE_ELEMENT_TRADE, trade))

class Client(observer.Subject):
	def __init__(self, currencies):
		self.__thread = None
		self.__queue = Queue.Queue()
		self.__wsClient = WS2Client(currencies, self.__queue)
		self.__stopped = False
		self.__tradeEvent = observer.Event()
		self.__tickerEvent = observer.Event()

	def getTradeEvent(self):
		return self.__tradeEvent

	def getTickerEvent(self):
		return self.__tickerEvent

	def __threadMain(self):
		self.__wsClient.connect()
		self.__wsClient.run()

	def start(self):
		if self.__thread == None:
			self.__thread = threading.Thread(target=self.__threadMain)
			self.__thread.start()
		else:
			raise Exception("Already running")

	def stop(self):
		self.__stopped = True
		if self.__thread != None:
			self.__wsClient.close()

	def join(self):
		if self.__thread != None:
			self.__thread.join()

	def eof(self):
		return self.__stopped

	def dispatch(self):
		# TODO: Optimize this to process more than one element at a time.
		try:
			objType, obj = self.__queue.get(True, 1)
			if objType == WS2Client.QUEUE_ELEMENT_TICKER:
				self.__tickerEvent.emit(obj)
			elif objType == WS2Client.QUEUE_ELEMENT_TRADE:
				self.__tradeEvent.emit(obj)
			else:
				logger.error("Invalid object received to dispatch: %s" % (obj))
		except Queue.Empty:
			pass

	def peekDateTime(self):
		# Return None since this is a realtime subject.
		return None

