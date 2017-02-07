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

import json
import urllib

import pyalgotrade
from pyalgotrade.websocket import client
import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger("pusher")


# Pusher protocol reference: http://pusher.com/docs/pusher_protocol
# Every message on a Pusher WebSocket connection is packaged as an event.
# The data field is sent as a string (check 'Double encoding' in the protocol reference). If dataIsJSON is True, it is decoded.
class Event(object):
    def __init__(self, eventDict, dataIsJSON):
        self.__eventDict = eventDict
        self.__data = eventDict.get("data")
        if self.__data is not None and dataIsJSON:
            self.__data = json.loads(self.__data)

    def __str__(self):
        return str(self.__eventDict)

    def getDict(self):
        return self.__eventDict

    def getData(self):
        return self.__data

    def getType(self):
        return self.__eventDict.get("event")


class PingKeepAliveMgr(client.KeepAliveMgr):
    def __init__(self, wsClient, maxInactivity, responseTimeout):
        super(PingKeepAliveMgr, self).__init__(wsClient, maxInactivity, responseTimeout)

    # Override to send the keep alive msg.
    def sendKeepAlive(self):
        logger.debug("Sending pusher:ping.")
        self.getWSClient().sendPing()

    # Return True if the response belongs to a keep alive message, False otherwise.
    def handleResponse(self, msg):
        ret = msg.get("event") == "pusher:pong"
        if ret:
            logger.debug("Received pusher:pong.")
        return ret


class WebSocketClient(client.WebSocketClientBase):
    def __init__(self, appKey, protocol=5, maxInactivity=120, responseTimeout=30):
        params = {
            "protocol": protocol,
            "client": "Python-PyAlgoTrade",
            "version": pyalgotrade.__version__
            }
        url = "ws://ws.pusherapp.com/app/%s?%s" % (appKey, urllib.urlencode(params))
        super(WebSocketClient, self).__init__(url)
        self.setKeepAliveMgr(PingKeepAliveMgr(self, maxInactivity, responseTimeout))

    def sendEvent(self, eventType, eventData):
        msgDict = {"event": eventType}
        if eventData:
            msgDict["data"] = eventData
        msg = json.dumps(msgDict)
        self.send(msg, False)

    def subscribeChannel(self, channel):
        self.sendEvent("pusher:subscribe", {"channel": channel})

    def sendPing(self):
        self.sendEvent("pusher:ping", None)

    def sendPong(self):
        self.sendEvent("pusher:pong", None)

    def onMessage(self, msg):
        eventType = msg.get("event")

        if eventType == "pusher:error":
            self.onError(Event(msg, False))
        elif eventType == "pusher:ping":
            self.sendPong()
        elif eventType == "pusher:connection_established":
            self.onConnectionEstablished(Event(msg, True))
        elif eventType == "pusher_internal:subscription_succeeded":
            self.onSubscriptionSucceeded(Event(msg, True))
        else:
            # If we can't handle the message, notify the most concrete class.
            self.onUnknownEvent(Event(msg, False))

    ######################################################################
    # Override for Pusher specific events.

    def onConnectionEstablished(self, event):
        pass

    def onSubscriptionSucceeded(self, event):
        pass

    def onError(self, event):
        raise NotImplementedError()

    def onUnknownEvent(self, event):
        raise NotImplementedError()
