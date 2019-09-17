# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

from six.moves import queue
import websocket

import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger(__name__)


# Base clase for websocket clients.
# To use it call connect and startClient, and stopClient.
# Note that this class has thread affinity, so build it and use it from the same thread.
class WebSocketClientBase(websocket.WebSocketApp):
    def __init__(self, url, ping_interval, ping_timeout):
        super(WebSocketClientBase, self).__init__(
            url, on_message=self.onMessage, on_open=self._on_opened, on_close=self._on_closed, on_error=self.onError
        )
        self.__connected = False
        self.__ping_interval = ping_interval
        self.__ping_timeout = ping_timeout
        self.__initialized = threading.Event()

    def _on_opened(self):
        self.__connected = True
        self.onOpened()

    def _on_closed(self, code, reason):
        if self.__connected:
            self.__connected = False
            self.onClosed(code, reason)

    def setInitialized(self):
        assert self.isConnected()
        self.__initialized.set()

    def waitInitialized(self, timeout):
        return self.__initialized.wait(timeout)

    def isConnected(self):
        return self.__connected

    def startClient(self):
        self.run_forever(ping_interval=self.__ping_interval, ping_timeout=self.__ping_timeout)

    def stopClient(self):
        try:
            if self.__connected:
                self.close()
        except Exception as e:
            logger.error("Failed to close connection: %s" % e)

    ######################################################################
    # Overrides

    def onOpened(self):
        pass

    def onMessage(self, msg):
        raise NotImplementedError()

    def onClosed(self, code, reason):
        pass

    def onDisconnectionDetected(self):
        pass

    def onError(self, exception):
        pass


# Base clase for threads that will run a WebSocketClientBase instances.
class WebSocketClientThreadBase(threading.Thread):
    def __init__(self, wsCls, *args, **kwargs):
        super(WebSocketClientThreadBase, self).__init__()
        self.__queue = queue.Queue()
        self.__wsClient = None
        self.__wsCls = wsCls
        self.__args = args
        self.__kwargs = kwargs

    def getQueue(self):
        return self.__queue

    def waitInitialized(self, timeout):
        return self.__wsClient is not None and self.__wsClient.waitInitialized(timeout)

    def run(self):
        # We create the WebSocketClient right in the thread, instead of doing so in the constructor,
        # because it has thread affinity.
        try:
            self.__wsClient = self.__wsCls(self.__queue, *self.__args, **self.__kwargs)
            logger.debug("Running websocket client")
            self.__wsClient.startClient()
        except Exception as e:
            logger.exception("Unhandled exception %s" % e)
            self.__wsClient.stopClient()

    def stop(self):
        try:
            if self.__wsClient is not None:
                logger.debug("Stopping websocket client")
                self.__wsClient.stopClient()
        except Exception as e:
            logger.error("Error stopping websocket client: %s" % e)
