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

# Coinbase protocol reference: Check https://docs.exchange.coinbase.com/

import json

from pyalgotrade.websocket import client
from pyalgotrade.coinbase import messages


class KeepAliveMgr(client.KeepAliveMgr):
    def sendKeepAlive(self):
        pass

    def handleResponse(self, msg):
        return False


class WebSocketClient(client.WebSocketClientBase):
    URL = "wss://ws-feed.exchange.coinbase.com"
    MAX_INACTIVITY = 120

    def __init__(self, productId, url=URL):
        super(WebSocketClient, self).__init__(url)
        self.__productId = productId
        self.__lastSequenceNr = None
        self.setKeepAliveMgr(KeepAliveMgr(self, WebSocketClient.MAX_INACTIVITY, 0.1))

    def __checkSequenceMismatch(self, msgDict):
        sequence_nr = msgDict.get("sequence")
        assert sequence_nr is not None, "Sequence number is missing"
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
            "product_id": self.__productId
        })

    def onMessage(self, msgDict):
        msg_type = msgDict.get("type")

        if msg_type == "error":
            self.onError(msgDict.get("message"))
        else:
            self.__checkSequenceMismatch(msgDict)

            if msg_type == "received":
                self.onOrderReceived(messages.Received(msgDict))
            elif msg_type == "open":
                self.onOrderOpen(messages.Open(msgDict))
            elif msg_type == "done":
                self.onOrderDone(messages.Done(msgDict))
            elif msg_type == "match":
                self.onOrderMatch(messages.Match(msgDict))
            elif msg_type == "change":
                self.onOrderChange(messages.Change(msgDict))
            else:
                self.onUnknownMessage(msgDict)

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

