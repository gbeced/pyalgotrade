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

import time
import json
import hashlib
import binascii
import hmac
import base64

import tornado
from ws4py.client import tornadoclient

from pyalgotrade.mtgox import base

def get_hex_md5(value):
	m = hashlib.md5()
	m.update(value)
	return m.hexdigest()

def sign_request(request, apiSecret):
	return hmac.new(base64.b64decode(apiSecret), request, hashlib.sha512).digest()

def apikey_as_binary(key):
	return binascii.unhexlify(key.replace("-", ""))

# This class is responsible for sending keep alive messages and detecting disconnections
# from the server.
class KeepAliveMgr:
	HEART_BEAT_MSG = "keep-alive-msg"

	def __init__(self, wsClient, ioLoop, frequency, maxMsgsWithoutResponse):
		assert(maxMsgsWithoutResponse > 0)
		assert(frequency > 0)
		self.__wsClient = wsClient
		self.__callback = tornado.ioloop.PeriodicCallback(self.keepAlive, frequency, ioLoop)
		self.__msgsWithoutResponse = 0
		self.__maxMsgsWithoutResponse = maxMsgsWithoutResponse

	def keepAlive(self):
		if self.__msgsWithoutResponse >= self.__maxMsgsWithoutResponse:
			self.__wsClient.onDisconnectionDetected()
		else:
			try:
				self.__wsClient.send(KeepAliveMgr.HEART_BEAT_MSG, False)
				self.__msgsWithoutResponse += 1
			except Exception:
				self.__wsClient.onDisconnectionDetected()

	def handleResponse(self, data):
		# MtGox sends back the invalid message response as a remark.
		ret = False
		if data["op"] == "remark":
			if data.get("debug", {}).get("data_raw") == KeepAliveMgr.HEART_BEAT_MSG:
				self.__msgsWithoutResponse = 0
				ret = True
		return ret

	def start(self):
		self.__callback.start()

	def stop(self):
		self.__callback.stop()

class WebSocketClientBase(tornadoclient.TornadoWebSocketClient):
	KEEP_ALIVE_FREQUENCY = 5*1000
	KEEP_ALIVE_MAX_MSG = 5

	def __init__(self, url):
		tornadoclient.TornadoWebSocketClient.__init__(self, url)
		self.__keepAliveMgr = None
		self.__connected = False

	# This is to avoid a stack trace because TornadoWebSocketClient is not implementing _cleanup.
	def _cleanup(self):
		ret = None
		try:
			ret = tornadoclient.TornadoWebSocketClient._cleanup(self)
		except Exception:
			pass
		return ret

	def received_message(self, message):
		data = json.loads(message.data)

		if self.__keepAliveMgr == None or not self.__keepAliveMgr.handleResponse(data):
			self.onMessage(data)

	def opened(self):
		self.__connected = True
		if WebSocketClientBase.KEEP_ALIVE_FREQUENCY:
			self.__keepAliveMgr = KeepAliveMgr(self, tornado.ioloop.IOLoop.instance(), WebSocketClientBase.KEEP_ALIVE_FREQUENCY, WebSocketClientBase.KEEP_ALIVE_MAX_MSG)
			self.__keepAliveMgr.start()
		self.onOpened()

	def closed(self, code, reason):
		self.__connected = False
		if self.__keepAliveMgr:
			self.__keepAliveMgr.stop()
			self.__keepAliveMgr = None
		tornado.ioloop.IOLoop.instance().stop()

		self.onClosed(code, reason)

	def handshake_ok(self):
		pass

	def isConnected(self):
		return self.__connected

	def startClient(self):
		tornado.ioloop.IOLoop.instance().start()

	def stopClient(self):
		self.close_connection()

	def onOpened(self):
		raise NotImplementedError()

	def onMessage(self, data):
		raise NotImplementedError()

	def onClosed(self, code, reason):
		raise NotImplementedError()

	def onDisconnectionDetected(self):
		raise NotImplementedError()

# https://en.bitcoin.it/wiki/MtGox/API/Streaming
class WebSocketClient(WebSocketClientBase):
	DEPTH_NOTIFICATIONS_CHANNEL = "24e67e0d-1cad-4cc0-9e7a-f8523ef460fe"

	# currency is the account's currency.
	def __init__(self, currency, apiKey, apiSecret, ignoreMultiCurrency=False):
		currencies = [currency]
		url = 'ws://websocket.mtgox.com/mtgox?Currency=%s' % (",".join(currencies))
		WebSocketClientBase.__init__(self, url)
		self.__nonce = None
		self.__apiKey = apiKey
		self.__apiSecret = apiSecret
		self.__ignoreMultiCurrency = ignoreMultiCurrency

	def __getNonce(self):
		# nonce must be greater than the last one.
		ret = int(time.time()*1000000)
		if ret == self.__nonce:
			ret += 1
		self.__nonce = ret
		return ret

	def onMessage(self, data):
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

	def subscribePrivateChannel(self, privateKeyId):
		msg = json.dumps({"op":"mtgox.subscribe", "key":privateKeyId})
		self.send(msg, False)

	def subscribeChannel(self, channelId):
		msg = json.dumps({"op":"subscribe", "channel":channelId})
		self.send(msg, False)

	def unsubscribeChannel(self, channelId):
		msg = json.dumps({"op":"unsubscribe", "channel":channelId})
		self.send(msg, False)

	def __authCall(self, call, params={}, item="BTC", currency=""):
		# https://en.bitcoin.it/wiki/MtGox/API/Streaming#Authenticated_commands
		# If 'Invalid call' remark is received, this is probably due to a bad nonce.
		nonce =  self.__getNonce()
		requestId = get_hex_md5(str(nonce))
		requestDict = {
				"id":requestId,
				"call":call,
				"nonce":nonce,
				"params":params,
				"item":item,
				"currency":currency,
				}
		request = json.dumps(requestDict)

		# https://en.bitcoin.it/wiki/MtGox/API/HTTP
		binaryKey = apikey_as_binary(self.__apiKey)
		signature = sign_request(request, self.__apiSecret)
		requestDict = {
				"op":"call",
				"id":requestId,
				"call":base64.b64encode(binaryKey + signature + request),
				"context":"mtgox.com",
				}
		msg = json.dumps(requestDict)
		self.send(msg, False)
		return requestId

	# def createOrder(self, orderType, amount, currency):
	# 	return self.__authCall("order/add", {"type":orderType, "amount":amount}, currency=currency)

	# def requestPrivateKeyId(self):
	# 	return self.__authCall("private/idkey")

	def onPrivate(self, data):
		if data["private"] == "ticker":
			self.onTicker( base.Ticker(data["ticker"]) )
		elif data["private"] == "trade":
			# From https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1:
			# A trade can appear in more than one currency, to ignore duplicates,
			# use only the trades having primary =Y
			if self.__ignoreMultiCurrency == False or data["trade"]["primary"] == "Y":
				self.onTrade( base.Trade(data["trade"]) )
		elif data["private"] == "depth":
			self.onDepth( base.Depth(data["depth"]) )
		elif data["private"] == "user_order":
			self.onUserOrder( base.UserOrder(data["user_order"]) )
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

	def onUserOrder(self, userOrder):
		pass

