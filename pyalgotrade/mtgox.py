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

class Price:
	def __init__(self, priceDict):
		self.__value = float(priceDict["value"])
		self.__currency = priceDict["currency"]

	def getValue(self):
		return self.__value

	def getCurrency(self):
		return self.__currency

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
			self.onTicker(data["ticker"])
		elif data["private"] == "trade":
			# From https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1:
			# A trade can appear in more than one currency, to ignore duplicates,
			# use only the trades having primary =Y
			if data["trade"]["primary"] == "Y":
				self.onTrade(data["trade"])
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

	def onTicker(self, data):
		pass

	def onTrade(self, data):
		pass

	def onDepth(self, data):
		pass

