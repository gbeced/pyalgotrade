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

import common
import abc


class Message(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, msgDict):
        self._msgDict = msgDict

    @abc.abstractmethod
    def hasSequence(self):
        raise NotImplementedError()

    def getDict(self):
        return self._msgDict


class Error(Message):
    def hasSequence(self):
        return False

    def getMessage(self):
        return self.getDict()["message"]


class Subscriptions(Message):
    def hasSequence(self):
        return False

    def getChannels(self):
        return self.getDict()["channels"]


class OrderMessage(Message):
    def hasSequence(self):
        return True

    def getSequence(self):
        return self.getDict()["sequence"]

    def getTime(self):
        return common.parse_timestamp(self.getDict()["time"])


class Received(OrderMessage):
    def getOrderId(self):
        return self.getDict()["order_id"]

    def getSize(self):
        return float(self.getDict()["size"])

    def getPrice(self):
        return float(self.getDict()["price"])

    def getSide(self):
        return self.getDict()["side"]


class Open(OrderMessage):
    def getOrderId(self):
        return self.getDict()["order_id"]

    def getPrice(self):
        return float(self.getDict()["price"])

    def getRemainingSize(self):
        return float(self.getDict()["remaining_size"])

    def getSide(self):
        return self.getDict()["side"]


class Done(OrderMessage):
    def getPrice(self):
        return float(self.getDict()["price"])

    def getOrderId(self):
        return self.getDict()["order_id"]

    def getReason(self):
        return self.getDict()["reason"]

    def getSide(self):
        return self.getDict()["side"]

    def getRemainingSize(self):
        return float(self.getDict()["remaining_size"])

    def hasRemainingSize(self):
        return float(self.getDict().get("remaining_size", 0.0)) > 0


class Match(OrderMessage):
    def getTradeId(self):
        return self.getDict()["trade_id"]

    def getMakerOrderId(self):
        return self.getDict()["maker_order_id"]

    def getTakerOrderId(self):
        return self.getDict()["taker_order_id"]

    def getSize(self):
        return float(self.getDict()["size"])

    def getPrice(self):
        return float(self.getDict()["price"])

    def getSide(self):
        return self.getDict()["side"]


class Change(OrderMessage):
    def getOrderId(self):
        return self.getDict()["order_id"]

    def getNewSize(self):
        return float(self.getDict()["new_size"])

    def getOldSize(self):
        return float(self.getDict()["old_size"])

    def getPrice(self):
        return float(self.getDict()["price"])

    def getSide(self):
        return self.getDict()["side"]
