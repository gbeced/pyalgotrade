# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

import json
import time

from ws4py.client import tornadoclient
import tornado
import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger("websocket")


# This class is responsible for sending keep alive messages and detecting disconnections
# from the server.
class KeepAliveMgr(object):
    def __init__(self, wsClient, maxInactivity, responseTimeout):
        assert(maxInactivity > 0)
        assert(responseTimeout > 0)
        self.__callback = None
        self.__wsClient = wsClient
        self.__activityTimeout = maxInactivity
        self.__responseTimeout = responseTimeout
        self.__lastSeen = None
        self.__kaSent = None  # timestamp when the last keep alive was sent.

    def _keepAlive(self):
        if self.__lastSeen is None:
            return

        # Check if we're under the inactivity threshold.
        inactivity = (time.time() - self.__lastSeen)
        if inactivity <= self.__activityTimeout:
            return

        # Send keep alive if it was not sent,
        # or check if we have to timeout waiting for the keep alive response.
        try:
            if self.__kaSent is None:
                self.sendKeepAlive()
                self.__kaSent = time.time()
            elif (time.time() - self.__kaSent) > self.__responseTimeout:
                self.__wsClient.onDisconnectionDetected()
        except Exception:
            # Treat an error sending the keep-alive as a diconnection.
            # print "Error sending keep alive", e
            self.__wsClient.onDisconnectionDetected()

    def getWSClient(self):
        return self.__wsClient

    def setAlive(self):
        self.__lastSeen = time.time()
        self.__kaSent = None

    def start(self):
        # Check every second.
        self.__callback = tornado.ioloop.PeriodicCallback(self._keepAlive, 1000, self.__wsClient.getIOLoop())
        self.__callback.start()

    def stop(self):
        if self.__callback is not None:
            self.__callback.stop()

    # Override to send the keep alive msg.
    def sendKeepAlive(self):
        raise NotImplementedError()

    # Return True if the response belongs to a keep alive message, False otherwise.
    def handleResponse(self, msg):
        raise NotImplementedError()


# Base clase for websocket clients.
# To use it call connect and startClient, and stopClient.
class WebSocketClientBase(tornadoclient.TornadoWebSocketClient):
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

    def getIOLoop(self):
        return tornado.ioloop.IOLoop.instance()

    # Must be set before calling startClient().
    def setKeepAliveMgr(self, keepAliveMgr):
        if self.__keepAliveMgr is not None:
            raise Exception("KeepAliveMgr already set")
        self.__keepAliveMgr = keepAliveMgr

    def received_message(self, message):
        try:
            msg = json.loads(message.data)

            if self.__keepAliveMgr is not None:
                self.__keepAliveMgr.setAlive()
                if self.__keepAliveMgr.handleResponse(msg):
                    return

            self.onMessage(msg)
        except Exception, e:
            self.onUnhandledException(e)

    def opened(self):
        self.__connected = True
        if self.__keepAliveMgr is not None:
            self.__keepAliveMgr.start()
            self.__keepAliveMgr.setAlive()
        self.onOpened()

    def closed(self, code, reason=None):
        self.__connected = False
        if self.__keepAliveMgr:
            self.__keepAliveMgr.stop()
            self.__keepAliveMgr = None
        tornado.ioloop.IOLoop.instance().stop()

        self.onClosed(code, reason)

    def isConnected(self):
        return self.__connected

    def startClient(self):
        tornado.ioloop.IOLoop.instance().start()

    def stopClient(self):
        self.close_connection()

    ######################################################################
    # Overrides

    def onUnhandledException(self, exception):
        logger.critical("Unhandled exception", exc_info=exception)
        raise

    def onOpened(self):
        pass

    def onMessage(self, msg):
        raise NotImplementedError()

    def onClosed(self, code, reason):
        pass

    def onDisconnectionDetected(self):
        pass
