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

# Coinbase protocol reference: Check https://docs.gdax.com/

import json

from pyalgotrade.websocket import client
from pyalgotrade.coinbase import messages
from pyalgotrade.coinbase import common


# No keep alive messages.
class KeepAliveMgr(client.KeepAliveMgr):
    def sendKeepAlive(self):
        pass

    def handleResponse(self, msg):
        return False


class WebSocketClient(client.WebSocketClientBase):
    class Event:
        ERROR = 1
        CONNECTED = 2
        DISCONNECTED = 3
        ORDER_MATCH = 4
        ORDER_RECEIVED = 5
        ORDER_OPEN = 6
        ORDER_DONE = 7
        ORDER_CHANGE = 8
        SEQ_NR_MISMATCH = 9

    def __init__(self, productId, url, queue, maxInactivity=120):
        """
        Base class for Coinbase websocket feed responsible for processing the full channel.
        """

        super(WebSocketClient, self).__init__(url)
        self.__productId = productId
        self.__queue = queue
        self.__lastSequenceNr = None
        # There are no keep alive messages so as soon as maxInactivity is reached treat that as a disconnection.
        keepAliveResponseTimeout = 0.1
        self.setKeepAliveMgr(KeepAliveMgr(self, maxInactivity, keepAliveResponseTimeout))

    def _checkSequence(self, msg):
        sequence_nr = msg.getSequence()
        if self.__lastSequenceNr is None:
            # This is for the first message received.
            self.__lastSequenceNr = sequence_nr
        elif sequence_nr > self.__lastSequenceNr:
            diff = sequence_nr - self.__lastSequenceNr
            if diff != 1:
                self.onSequenceMismatch(self.__lastSequenceNr, sequence_nr)
            self.__lastSequenceNr = sequence_nr
        else:
            self.onSequenceMismatch(self.__lastSequenceNr, sequence_nr)

    def sendJSON(self, msgDict):
        self.send(json.dumps(msgDict))

    def onOpened(self):
        self.sendJSON({
            "type": "subscribe",
            "product_ids": [self.__productId],
            "channels": ["full"]
        })
        common.logger.info("Connection opened.")
        self.__queue.put((WebSocketClient.Event.CONNECTED, None))

    def onMessage(self, msgDict):
        msg_dispatch_table = {
            "error": {
                "msg_class": messages.Error,
                "handler": self.onError,
            },
            "received": {
                "msg_class": messages.Received,
                "handler": self.onOrderReceived,
            },
            "open": {
                "msg_class": messages.Open,
                "handler": self.onOrderOpen,
            },
            "done": {
                "msg_class": messages.Done,
                "handler": self.onOrderDone,
            },
            "match": {
                "msg_class": messages.Match,
                "handler": self.onOrderMatch,
            },
            "change": {
                "msg_class": messages.Change,
                "handler": self.onOrderChange,
            },
            "subscriptions": {
                "msg_class": messages.Subscriptions,
                "handler": self.onSubscriptions,
            },
        }

        msg_type = msgDict.get("type")
        msg_dispatch_entry = msg_dispatch_table.get(msg_type)
        if msg_dispatch_entry is None:
            self.onUnknownMessage(msgDict)
        else:
            msg = msg_dispatch_entry["msg_class"](msgDict)
            if msg.hasSequence():
                self._checkSequence(msg)
            msg_dispatch_entry["handler"](msg)

    ######################################################################
    # WebSocketClientBase events.

    def onConnectionRefused(self, code, reason):
        common.logger.error("Connection refused. Code: %s. Reason: %s." % (code, reason))

    def onClosed(self, code, reason):
        common.logger.info("Closed. Code: %s. Reason: %s." % (code, reason))
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    def onDisconnectionDetected(self):
        common.logger.warning("Disconnection detected.")
        try:
            self.stopClient()
        except Exception as e:
            common.logger.error("Error stopping websocket client: %s." % (str(e)))
        self.__queue.put((WebSocketClient.Event.DISCONNECTED, None))

    ######################################################################
    # Coinbase specific

    def onError(self, msg):
        common.logger.error(msg.getMessage())
        self.__queue.put((WebSocketClient.Event.ERROR, msg))

    def onUnknownMessage(self, msgDict):
        common.logger.warning("Unknown message %s" % msgDict)

    def onSequenceMismatch(self, lastValidSequence, currentSequence):
        common.logger.warning("Sequence jumped from %s to %s" % (lastValidSequence, currentSequence))
        self.__queue.put((WebSocketClient.Event.SEQ_NR_MISMATCH, currentSequence))

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

    def onSubscriptions(self, msg):
        common.logger.info("Subscriptions: %s" % msg.getChannels())


class WebSocketClientThread(client.WebSocketClientThreadBase):
    """
    This thread class is responsible for running a WebSocketClient.
    """

    def __init__(self, productId, url, maxInactivity=120):
        super(WebSocketClientThread, self).__init__(
            lambda queue: WebSocketClient(productId, url, queue, maxInactivity)
        )
