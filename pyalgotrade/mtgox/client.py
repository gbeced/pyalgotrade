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


from pyalgotrade import observer
import pyalgotrade.logger
import wsclient
import httpclient

import threading
import Queue
import time

logger = pyalgotrade.logger.getLogger("mtgox")

# This class is responsible for handling events running in the WebSocketClient thread and putting
# them in a queue.
class WSClient(wsclient.WebSocketClient):

	# Events
	ON_TICKER = 1
	ON_TRADE = 2
	ON_USER_ORDER = 3
	ON_RESULT = 4
	ON_REMARK = 5
	ON_CONNECTED = 6
	ON_DISCONNECTED = 7

	# currency is the account's currency.
	def __init__(self, queue, currency, apiKey, apiSecret, ignoreMultiCurrency):
		wsclient.WebSocketClient.__init__(self, currency, apiKey, apiSecret, ignoreMultiCurrency)
		self.__queue = queue

	def onOpened(self):
		self.__queue.put((WSClient.ON_CONNECTED, None))

	def onClosed(self, code, reason):
		logger.info("Closed. Code: %s. Reason: %s." % (code, reason))

	def onDisconnectionDetected(self):
		self.close_connection()
		self.__queue.put((WSClient.ON_DISCONNECTED, None))

	def onSubscribe(self, data):
		logger.info("Subscribe: %s." % (data))

	def onUnsubscribe(self, data):
		logger.info("Unsubscribe: %s." % (data))

	def onRemark(self, data):
		if "id" in data:
			self.__queue.put((WSClient.ON_REMARK, (data["id"], data)))
		else:
			logger.info("Remark: %s" % (data))

	def onUnknownOperation(self, operation, data):
		logger.warning("Unknown operation %s: %s" % (operation, data))

	def onResult(self, data):
		self.__queue.put((WSClient.ON_RESULT, (data["id"], data["result"])))

	def onTicker(self, ticker):
		self.__queue.put((WSClient.ON_TICKER, ticker))

	def onTrade(self, trade):
		self.__queue.put((WSClient.ON_TRADE, trade))

	def onUserOrder(self, userOrder):
		self.__queue.put((WSClient.ON_USER_ORDER, userOrder))

class Client(observer.Subject):
	"""This class is responsible for all trading interaction with MtGox.

	:param currency: The account's currency. Valid values are: USD, AUD, CAD, CHF, CNY, DKK, EUR, GBP, HKD, JPY, NZD, PLN, RUB, SEK, SGD, THB, NOK or CZK.
	:type currency: string.
	:param apiKey: Your API key. Set this to None for paper trading.
	:type apiKey: string.
	:param apiSecret: Your API secret. Set this to None for paper trading.
	:type apiSecret: string.
	:param ignoreMultiCurrency: Ignore multi currency trades.
	:type ignoreMultiCurrency: boolean.

	.. note::
		For apiKey and apiSecret check the **Application and API access** section in mtgox.com.
	"""
	QUEUE_TIMEOUT = 0.01

	# currency is the account's currency.
	def __init__(self, currency, apiKey, apiSecret, ignoreMultiCurrency=False):
		if currency not in ["USD", "AUD", "CAD", "CHF", "CNY", "DKK", "EUR", "GBP", "HKD", "JPY", "NZD", "PLN", "RUB", "SEK", "SGD", "THB", "NOK", "CZK"]:
			raise Exception("Invalid currency")

		self.__currency = currency
		self.__apiKey = apiKey
		self.__apiSecret = apiSecret
		self.__ignoreMultiCurrency = ignoreMultiCurrency

		self.__thread = None
		self.__queue = Queue.Queue()
		self.__initializationFailed = None
		self.__stopped = False
		self.__tickerEvent = observer.Event()
		self.__tradeEvent = observer.Event()
		self.__userOrderEvent = observer.Event()
		self.__wsClient = None
		self.__enableReconnection = True

		# Build papertrading/livetrading objects.
		if apiKey == None or  apiSecret == None:
			self.__paperTrading = True
		else:
			self.__paperTrading = False
			self.__httpClient = httpclient.HTTPClient(apiKey, apiSecret, currency)

	def getCurrency(self):
		return self.__currency

	def setEnableReconnection(self, enable):
		self.__enableReconnection = enable

	def __threadMain(self):
		self.__wsClient.startClient()
		# logger.info("Thread finished.")

	def __initializeClient(self):
		logger.info("Initializing MtGox client.")

		# We use the streaming client only to get updates and not to send requests (using authCall)
		# because when placing orders sometimes we were receving the order update before the result
		# with the order GUID.
		self.__wsClient = WSClient(self.__queue, self.__currency, self.__apiKey, self.__apiSecret, self.__ignoreMultiCurrency)
		self.__initializationFailed = None
		self.__wsClient.connect()

		# Start the thread that will run the client.
		self.__thread = threading.Thread(target=self.__threadMain)
		self.__thread.start()

		# Wait for initialization to complete.
		while self.__initializationFailed == None and self.__thread.is_alive():
			self.dispatchImpl([WSClient.ON_CONNECTED])
		if self.__initializationFailed == False:
			logger.info("Initialization ok.")
		else:
			logger.error("Initialization failed.")
		return self.__initializationFailed == False

	def __onConnected(self):
		logger.info("Connection opened.")

		try:
			# Remove depth notifications channel.
			self.__wsClient.unsubscribeChannel(wsclient.WebSocketClient.DEPTH_NOTIFICATIONS_CHANNEL)

			if self.__paperTrading == False:
				# Request the Private Id Key and subsribe to private channel.
				logger.info("Requesting private id key.")
				response = self.__httpClient.requestPrivateKeyId()
				if response.get("result") != "success":
					raise Exception("Invalid response %s" % (response))
				privateIdKey = response.get("return")
				if privateIdKey == None:
					raise Exception("Invalid response %s" % (response))
				logger.info("Subscribing to private channel.")
				self.__wsClient.subscribePrivateChannel(privateIdKey)
			self.__initializationFailed = False
		except Exception, e:
			self.__initializationFailed = True
			logger.error("Error: %s" % str(e))

	def __onDisconnected(self):
		logger.error("Disconnection detected")
		if self.__enableReconnection:
			initialized = False
			while not self.__stopped and not initialized:
				logger.info("Reconnecting")
				initialized = self.__initializeClient()
				if not initialized:
					time.sleep(5)
		else:
			self.__stopped = True

	def getTickerEvent(self):
		return self.__tickerEvent

	def getTradeEvent(self):
		return self.__tradeEvent

	def getUserOrderEvent(self):
		return self.__userOrderEvent

	def start(self):
		if self.__thread != None:
			raise Exception("Already running")
		elif self.__initializeClient() == False:
			self.__stopped = True
			raise Exception("Initialization failed")

	def stop(self):
		try:
			self.__stopped = True
			if self.__thread != None and self.__thread.is_alive():
				logger.info("Shutting down MtGox client.")
				self.__wsClient.stopClient()
		except Exception, e:
			logger.error("Error shutting down MtGox client: %s" % (str(e)))

	def join(self):
		if self.__thread != None:
			self.__thread.join()

	def eof(self):
		return self.__stopped

	def dispatchImpl(self, eventFilter):
		try:
			eventType, eventData = self.__queue.get(True, Client.QUEUE_TIMEOUT)
			if eventFilter != None and eventType not in eventFilter:
				return

			if eventType == WSClient.ON_TICKER:
				self.__tickerEvent.emit(eventData)
			elif eventType == WSClient.ON_TRADE:
				self.__tradeEvent.emit(eventData)
			elif eventType == WSClient.ON_USER_ORDER:
				self.__userOrderEvent.emit(eventData)
			elif eventType == WSClient.ON_RESULT:
				requestId, result = eventData
				logger.info("Result: %s - %s" % (requestId, result))
			elif eventType == WSClient.ON_REMARK:
				requestId, data = eventData
				logger.info("Remark: %s - %s" % (requestId, data))
			elif eventType == WSClient.ON_CONNECTED:
				self.__onConnected()
			elif eventType == WSClient.ON_DISCONNECTED:
				self.__onDisconnected()
			else:
				logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
		except Queue.Empty:
			pass

	def dispatch(self):
		self.dispatchImpl(None)

	def peekDateTime(self):
		# Return None since this is a realtime subject.
		return None

	def getDispatchPriority(self):
		# The number is irrelevant since the broker and barfeed will set their priorities relative to this one.
		return 100

