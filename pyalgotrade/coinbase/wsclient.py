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

import pyalgotrade
from pyalgotrade.websocket import client
import pyalgotrade.logger
from pyalgotrade.coinbase import messages


logger = pyalgotrade.logger.getLogger("coinbase.wsclient")


class KeepAliveMgr(client.KeepAliveMgr):
    def sendKeepAlive(self):
        pass

    def handleResponse(self, msg):
        return False


class WebSocketClientBase(client.WebSocketClientBase):
    URL = "wss://ws-feed.exchange.coinbase.com"
    MAX_INACTIVITY = 120

    def __init__(self):
        super(WebSocketClientBase, self).__init__(WebSocketClientBase.URL)
        self.__last_sequence_nr = None
        self.setKeepAliveMgr(KeepAliveMgr(self, WebSocketClientBase.MAX_INACTIVITY, 1))

    def __checkSequenceMismatch(self, msgDict):
        sequence_nr = msgDict.get("sequence")
        if sequence_nr is None:
            logger.error("Sequence missing in message %s" % msgDict)
        elif self.__last_sequence_nr is None:
            # This is for the first message received.
            self.__last_sequence_nr = sequence_nr
        elif sequence_nr > self.__last_sequence_nr:
            diff = sequence_nr - self.__last_sequence_nr
            if diff != 1:
                self.onSequenceMismatch(self.__last_sequence_nr, sequence_nr)
            self.__last_sequence_nr = sequence_nr
        else:
            self.onSequenceMismatch(self.__last_sequence_nr, sequence_nr)

    def sendJSON(self, msgDict):
        self.send(json.dumps(msgDict))

    def onOpened(self):
        logger.info("Connection opened.")
        self.sendJSON({
            "type": "subscribe",
            "product_id": "BTC-USD"
        })

    def onMessage(self, msgDict):
        msg_type = msgDict.get("type")

        if msg_type == "error":
            self.onError(msgDict.get("message"))
        else:
            self.__checkSequenceMismatch(msgDict)
            logger.info(msgDict)

            if msg_type == "received":
                self.onReceived(messages.Received(msgDict))
            elif msg_type == "open":
                self.onOpen(messages.Open(msgDict))
            elif msg_type == "done":
                self.onDone(messages.Done(msgDict))
            elif msg_type == "match":
                self.onMatch(messages.Match(msgDict))
            elif msg_type == "change":
                self.onChange(messages.Change(msgDict))
            else:
                self.onUnknownMessage(msgDict)

    ######################################################################
    # Coinbase specific

    def onSequenceMismatch(self, lastValidSequence, currentSequence):
        logger.warning("Sequence jumped from %s to %s" % (lastValidSequence, currentSequence))

    def onUnknownMessage(self, msgDict):
        logger.warning("Unknown message: %s" % (msgDict))

    def onReceived(self, msg):
        pass

    def onOpen(self, msg):
        pass

    def onDone(self, msg):
        pass

    def onMatch(self, msg):
        pass

    def onChange(self, msg):
        pass

    def onError(self, message):
        logger.error(message)
