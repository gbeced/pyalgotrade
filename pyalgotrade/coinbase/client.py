# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

import threading
import Queue
import time

from pyalgotrade import observer
import pyalgotrade.logger
from pyalgotrade.coinbase import httpclient
from pyalgotrade.coinbase import wsclient

logger = pyalgotrade.logger.getLogger(__name__)


class WebSocketClient(wsclient.WebSocketClient):
    class Event:
        CONNECTED = 1
        DISCONNECTED = 2
        ORDER_MATCH = 3
        ORDER_RECEIVED = 4
        ORDER_OPEN = 5
        ORDER_DONE = 6
        ORDER_CHANGE = 7

    def __init__(self):
        super(WebSocketClient, self).__init__()
        self.__queue = Queue.Queue()

    def getQueue(self):
        return self.__queue

    def onOpened(self):
        super(WebSocketClient, self).onOpened()
        logger.info("Connection opened.")
        self.__queue.put((WebSocketClient.Event.CONNECTED, None))

    def onClosed(self, code, reason):
        logger.info("Closed. Code: %s. Reason: %s." % (code, reason))

    def onDisconnectionDetected(self):
        logger.warning("Disconnection detected.")
        self.stopClient()
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    ######################################################################
    # Coinbase specific

    def onSequenceMismatch(self, lastValidSequence, currentSequence):
        super(WebSocketClient, self).onSequenceMismatch()

    def onOrderReceived(self, msg):
        self.__queue.put((WebSocketClient.Event.ORDER_RECEIVED, msg))

    def onOrderOpen(self, msg):
        self.__queue.put((WebSocketClient.Event.ORDER_OPEN, msg))

    def onOrderDone(self, msg):
        self.__queue.put((WebSocketClient.Event.ORDER_DONE, msg))

    def onOrderMatch(self, msg):
        self.__queue.put((WebSocketClient.Event.ORDER_MATCH, msg))

    def onOrderChange(self, msg):
        self.__queue.put((WebSocketClient.Event.ORDER_CHANGE, msg))


class WebSocketClientThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.__wsClient = WebSocketClient()

    def isConnected(self):
        return self.__wsClient.isConnected()

    def getQueue(self):
        return self.__wsClient.getQueue()

    def start(self):
        logger.info("Connecting websocket client.")
        self.__wsClient.connect()
        threading.Thread.start(self)

    def run(self):
        self.__wsClient.startClient()

    def stop(self):
        try:
            logger.info("Stopping websocket client.")
            self.__wsClient.stopClient()
        except Exception, e:
            logger.error("Error stopping websocket client: %s." % (str(e)))


class Client(observer.Subject):
    QUEUE_TIMEOUT = 0.01

    def __init__(self):
        self.__stopped = False
        self.__httpClient = httpclient.HTTPClient()
        self.__orderEvents = observer.Event()
        self.__orderBookEvents = observer.Event()
        self.__wsClientThread = None

    def __connectWS(self, retry):
        assert self.__wsClientThread is None

        while True:
            self.__wsClientThread = WebSocketClientThread()
            self.__wsClientThread.start()
            while self.__wsClientThread.is_alive() and not self.__wsClientThread.isConnected():
                time.sleep(0.5)
            if self.__wsClientThread.isConnected() or not retry:
                break

    def __onConnected(self):
        # TODO: Generate an event so broker can refresh.
        pass

    def __onDisconnected(self):
        if not self.__stopped:
            self.__wsClientThread = None
            self.__connectWS(True)

    def __onOrderEvent(self, eventType, eventData):
        self.__orderEvents.emit(eventData)

    def getHTTPClient(self):
        return self.__httpClient

    def getOrderEvents(self):
        return self.__orderEvents

    def getOrderBookEvents(self):
        return self.__orderBookEvents

    def start(self):
        self.__connectWS(False)
        if not self.__wsClientThread.isConnected():
            raise Exception("Failed to connect websocket client")

    def stop(self):
        if self.__wsClientThread is not None:
            self.__wsClientThread.stop()
            self.__stopped = True

    def join(self):
        if self.__wsClientThread is not None:
            self.__wsClientThread.join()

    def eof(self):
        return self.__stopped

    def dispatch(self):
        ret = False

        try:
            eventType, eventData = self.__wsClientThread.getQueue().get(True, Client.QUEUE_TIMEOUT)

            ret = True
            if eventType == WebSocketClient.Event.CONNECTED:
                self.__onConnected()
            elif eventType == WebSocketClient.Event.DISCONNECTED:
                self.__onDisconnected()
            elif eventType in [
                WebSocketClient.Event.ORDER_MATCH,
                WebSocketClient.Event.ORDER_RECEIVED,
                WebSocketClient.Event.ORDER_OPEN,
                WebSocketClient.Event.ORDER_DONE,
                WebSocketClient.Event.ORDER_CHANGE
            ]:
                self.__onOrderEvent(eventType, eventData)
            else:
                logger.error("Invalid event received to dispatch: %s - %s" % (eventType, eventData))
                ret = False
        except Queue.Empty:
            pass

        return ret

    def peekDateTime(self):
        return None
