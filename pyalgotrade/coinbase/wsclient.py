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

# Coinbase protocol reference: Check https://docs.gdax.com/

import json

from pyalgotrade.websocket import client
from pyalgotrade.coinbase import messages


# No keep alive messages.
class KeepAliveMgr(client.KeepAliveMgr):
    def sendKeepAlive(self):
        pass

    def handleResponse(self, msg):
        return False


class WebSocketClient(client.WebSocketClientBase):
    def __init__(self, productId, url, maxInactivity=120):
        """
        Base class for Coinbase websocket feed responsible for processing the full channel.
        """

        super(WebSocketClient, self).__init__(url)
        self.__productId = productId
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

    def onError(self, errorMsg): # pragma: no cover
        pass

    def onUnknownMessage(self, msgDict): # pragma: no cover
        pass

    def onSequenceMismatch(self, lastValidSequence, currentSequence): # pragma: no cover
        pass

    def onOrderReceived(self, msg): # pragma: no cover
        pass

    def onOrderOpen(self, msg): # pragma: no cover
        pass

    def onOrderDone(self, msg): # pragma: no cover
        pass

    def onOrderMatch(self, msg): # pragma: no cover
        pass

    def onOrderChange(self, msg): # pragma: no cover
        pass

    def onSubscriptions(self, msg): # pragma: no cover
        pass
