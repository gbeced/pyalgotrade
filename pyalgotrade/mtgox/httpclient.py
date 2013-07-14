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

import base64
import time
import urllib
import urllib2
import json
import hmac
import hashlib

from pyalgotrade.mtgox import base

# https://en.bitcoin.it/wiki/MtGox/API/HTTP#Python
# https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1
class HTTPClient:
	USER_AGENT = "PyAlgoTrade"

	# currency is the account's currency.
	def __init__(self, apiKey, apiSecret, currency):
		self.__apiKey = apiKey
		self.__apiSecret = base64.b64decode(apiSecret)
		self.__currency = currency
		self.__nonce = None
		self.__baseUrl = "https://data.mtgox.com/api/1/"

	def __getNonce(self):
		# nonce must be greater than the last one.
		ret = int(time.time()*1000000)
		if ret == self.__nonce:
			ret += 1
		self.__nonce = ret
		return ret

	def __buildQuery(self, req={}):
		req["nonce"] = self.__getNonce()
		post_data = urllib.urlencode(req)
		headers = {}
		headers["User-Agent"] = HTTPClient.USER_AGENT
		headers["Rest-Key"] = self.__apiKey
		headers["Rest-Sign"] = base64.b64encode(str(hmac.HMAC(self.__apiSecret, post_data, hashlib.sha512).digest()))
		return (post_data, headers)

	def __sendRequest(self, url, params):
		data, headers = self.__buildQuery(params)
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req, data)
		return json.loads(response.read())

	def requestPrivateKeyId(self):
		url = self.__baseUrl + "generic/private/idkey"
		return self.__sendRequest(url, {})

	def getCurrency(self):
		return self.__currency

	def addOrder(self, orderType, amount, price = None):
		url = self.__baseUrl + "BTC%s/private/order/add" % (self.__currency)
		params = {
				"type":orderType,
				"amount_int" : base.to_amount_int(amount)
				}
		if price != None:
			params["price_int"] = base.to_value_int(self.__currency, price)
		return self.__sendRequest(url, params)

	def cancelOrder(self, orderId):
		url = self.__baseUrl + "BTC%s/private/order/cancel" % (self.__currency)
		params = {
				"oid":orderId,
				}
		return self.__sendRequest(url, params)

	def privateInfo(self):
		url = self.__baseUrl + "generic/private/info"
		return self.__sendRequest(url, {})

