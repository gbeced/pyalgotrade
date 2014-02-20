# PyAlgoTrade
#
# Copyright 2011-2013 Gabriel Martin Becedillas Ruiz
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
import hashlib
import binascii
import hmac
import base64

import tornado
from ws4py.client import tornadoclient

from pyalgotrade.mtgox import base


def get_hex_md5(value):
    m = hashlib.md5()
    m.update(value)
    return m.hexdigest()


def sign_request(request, apiSecret):
    return hmac.new(base64.b64decode(apiSecret), request, hashlib.sha512).digest()


def apikey_as_binary(key):
    return binascii.unhexlify(key.replace("-", ""))


# This class is responsible for sending keep alive messages and detecting disconnections
# from the server.
class KeepAliveMgr(object):
    HEART_BEAT_MSG = "keep-alive-msg"

    def __init__(self, wsClient, ioLoop, frequency, maxMsgsWithoutResponse):
        assert(maxMsgsWithoutResponse > 0)
        assert(frequency > 0)
        self.__wsClient = wsClient
        self.__callback = tornado.ioloop.PeriodicCallback(self.keepAlive, frequency, ioLoop)
        self.__msgsWithoutResponse = 0
        self.__maxMsgsWithoutResponse = maxMsgsWithoutResponse

    def keepAlive(self):
        if self.__msgsWithoutResponse >= self.__maxMsgsWithoutResponse:
            self.__wsClient.onDisconnectionDetected()
        else:
            try:
                self.__wsClient.send(KeepAliveMgr.HEART_BEAT_MSG, False)
                self.__msgsWithoutResponse += 1
            except Exception:
                self.__wsClient.onDisconnectionDetected()

    def handleResponse(self, data):
        # MtGox sends back the invalid message response as a remark.
        ret = False
        if data["op"] == "remark":
            if data.get("debug", {}).get("data_raw") == KeepAliveMgr.HEART_BEAT_MSG:
                self.__msgsWithoutResponse = 0
                ret = True
        return ret

    def start(self):
        self.__callback.start()

    def stop(self):
        self.__callback.stop()


class WebSocketClientBase(tornadoclient.TornadoWebSocketClient):
    KEEP_ALIVE_FREQUENCY = 5*1000
    KEEP_ALIVE_MAX_MSG = 5

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

    def received_message(self, message):
        data = json.loads(message.data)

        if self.__keepAliveMgr is None or not self.__keepAliveMgr.handleResponse(data):
            self.onMessage(data)

    def opened(self):
        self.__connected = True
        if WebSocketClientBase.KEEP_ALIVE_FREQUENCY:
            self.__keepAliveMgr = KeepAliveMgr(self, tornado.ioloop.IOLoop.instance(), WebSocketClientBase.KEEP_ALIVE_FREQUENCY, WebSocketClientBase.KEEP_ALIVE_MAX_MSG)
            self.__keepAliveMgr.start()
        self.onOpened()

    def closed(self, code, reason):
        self.__connected = False
        if self.__keepAliveMgr:
            self.__keepAliveMgr.stop()
            self.__keepAliveMgr = None
        tornado.ioloop.IOLoop.instance().stop()

        self.onClosed(code, reason)

    def handshake_ok(self):
        pass

    def isConnected(self):
        return self.__connected

    def startClient(self):
        tornado.ioloop.IOLoop.instance().start()

    def stopClient(self):
        self.close_connection()

    def onOpened(self):
        raise NotImplementedError()

    def onMessage(self, data):
        raise NotImplementedError()

    def onClosed(self, code, reason):
        raise NotImplementedError()

    def onDisconnectionDetected(self):
        raise NotImplementedError()


# List of public channels from https://mtgox.com/api/2/stream/list_public
class PublicChannels:
    PUBLIC_CHANNELS = {
        'depth.BTCAUD': '296ee352-dd5d-46f3-9bea-5e39dede2005',
        'depth.BTCCAD': '5b234cc3-a7c1-47ce-854f-27aee4cdbda5',
        'depth.BTCCHF': '113fec5f-294d-4929-86eb-8ca4c3fd1bed',
        'depth.BTCCNY': '0d1ecad8-e20f-459e-8bed-0bdcf927820f',
        'depth.BTCCZK': 'a7a970cf-4f6c-4d85-a74e-ac0979049b87',
        'depth.BTCDKK': '9219abb0-b50c-4007-b4d2-51d1711ab19c',
        'depth.BTCEUR': '057bdc6b-9f9c-44e4-bc1a-363e4443ce87',
        'depth.BTCGBP': '60c3af1b-5d40-4d0e-b9fc-ccab433d2e9c',
        'depth.BTCHKD': '049f65dc-3af3-4ffd-85a5-aac102b2a579',
        'depth.BTCINR': '414fdb18-8f70-471c-a9df-b3c2740727ea',
        'depth.BTCJPY': '94483e07-d797-4dd4-bc72-dc98f1fd39e3',
        'depth.BTCKRW': '0c84bda7-e613-4b19-ae2a-6d26412c9f70',
        'depth.BTCNOK': '66da7fb4-6b0c-4a10-9cb7-e2944e046eb5',
        'depth.BTCNZD': 'cedf8730-bce6-4278-b6fe-9bee42930e95',
        'depth.BTCPLN': 'e4ff055a-f8bf-407e-af76-676cad319a21',
        'depth.BTCRUB': 'd6412ca0-b686-464c-891a-d1ba3943f3c6',
        'depth.BTCSEK': '8f1fefaa-7c55-4420-ada0-4de15c1c38f3',
        'depth.BTCSGD': '41e5c243-3d44-4fad-b690-f39e1dbb86a8',
        'depth.BTCTHB': '67879668-532f-41f9-8eb0-55e7593a5ab8',
        'depth.BTCUSD': '24e67e0d-1cad-4cc0-9e7a-f8523ef460fe',
        'test': 'bad99f24-fa8b-4938-bfdf-0c1831fc6665',
        'ticker.BTCAUD': 'eb6aaa11-99d0-4f64-9e8c-1140872a423d',
        'ticker.BTCBTC': '13edff67-cfa0-4d99-aa76-52bd15d6a058',
        'ticker.BTCCAD': '10720792-084d-45ba-92e3-cf44d9477775',
        'ticker.BTCCHF': '2644c164-3db7-4475-8b45-c7042efe3413',
        'ticker.BTCCNY': 'c251ec35-56f9-40ab-a4f6-13325c349de4',
        'ticker.BTCCZK': '2a968b7f-6638-40ba-95e7-7284b3196d52',
        'ticker.BTCDKK': 'e5ce0604-574a-4059-9493-80af46c776b3',
        'ticker.BTCEUR': '0bb6da8b-f6c6-4ecf-8f0d-a544ad948c15',
        'ticker.BTCGBP': '7b842b7d-d1f9-46fa-a49c-c12f1ad5a533',
        'ticker.BTCHKD': 'd3ae78dd-01dd-4074-88a7-b8aa03cd28dd',
        'ticker.BTCINR': '55e5feb8-fea5-416b-88fa-40211541deca',
        'ticker.BTCJPY': 'a39ae532-6a3c-4835-af8c-dda54cb4874e',
        'ticker.BTCKRW': 'bf85048d-4db9-4dbe-9ca3-5b83a1a4186e',
        'ticker.BTCLTC': '48b6886f-49c0-4614-b647-ba5369b449a9',
        'ticker.BTCNMC': '36189b8c-cffa-40d2-b205-fb71420387ae',
        'ticker.BTCNOK': '7532e866-3a03-4514-a4b1-6f86e3a8dc11',
        'ticker.BTCNZD': '5ddd27ca-2466-4d1a-8961-615dedb68bf1',
        'ticker.BTCPLN': 'b4a02cb3-2e2d-4a88-aeea-3c66cb604d01',
        'ticker.BTCRUB': 'bd04f720-3c70-4dce-ae71-2422ab862c65',
        'ticker.BTCSEK': '6caf1244-655b-460f-beaf-5c56d1f4bea7',
        'ticker.BTCSGD': '2cb73ed1-07f4-45e0-8918-bcbfda658912',
        'ticker.BTCTHB': 'd58e3b69-9560-4b9e-8c58-b5c0f3fda5e1',
        'ticker.BTCUSD': 'd5f06780-30a8-4a48-a2f8-7ed181b4a13f',
        'ticker.LTCAUD': 'a046600a-a06c-4ebf-9ffb-bdc8157227e8',
        'ticker.LTCCAD': '18b55737-3f5c-4583-af63-6eb3951ead72',
        'ticker.LTCCNY': '0290378c-e3d7-4836-8cb1-2bfae20cc492',
        'ticker.LTCDKK': 'b10a706e-e8c7-4ea8-9148-669f86930b36',
        'ticker.LTCEUR': '491bc9bb-7cd8-4719-a9e8-16dad802ffac',
        'ticker.LTCGBP': '0102a446-e4d4-4082-8e83-cc02822f9172',
        'ticker.LTCJPY': '5ad8e40f-6df3-489f-9cf1-af28426a50cf',
        'ticker.LTCNOK': '13616ae8-9268-4a43-bdf7-6b8d1ac814a2',
        'ticker.LTCUSD': '1366a9f3-92eb-4c6c-9ccc-492a959eca94',
        'ticker.NMCAUD': '08c65460-cbd9-492e-8473-8507dfa66ae6',
        'ticker.NMCCAD': 'dc28033e-7506-484c-905d-1c811a613323',
        'ticker.NMCCNY': '249fdefd-c6eb-4802-9f54-064bc83908aa',
        'ticker.NMCEUR': 'd8512d04-f262-4a14-82f2-8e5c96c15e68',
        'ticker.NMCGBP': 'bf5126ba-5187-456f-8ae6-963678d0607f',
        'ticker.NMCJPY': '314e2b7a-a9fa-4249-bc46-b7f662ecbc3a',
        'ticker.NMCUSD': '9aaefd15-d101-49f3-a2fd-6b63b85b6bed',
        'trade.BTC': 'dbf1dee9-4f2e-4a08-8cb7-748919a71b21',
        'trade.lag': '85174711-be64-4de1-b783-0628995d7914'}

    @classmethod
    def getDepthChannel(cls, currency):
        return cls.PUBLIC_CHANNELS["depth.BTC%s" % (currency)]

    @classmethod
    def getTickerChannel(cls, currency):
        return cls.PUBLIC_CHANNELS["ticker.BTC%s" % (currency)]

    @classmethod
    def getTradeChannel(cls):
        return cls.PUBLIC_CHANNELS["trade.BTC"]


# https://en.bitcoin.it/wiki/MtGox/API/Streaming
class WebSocketClient(WebSocketClientBase):
    # currency is the account's currency.
    def __init__(self, currency, apiKey, apiSecret, ignoreMultiCurrency=False):
        currencies = [currency]
        url = 'ws://websocket.mtgox.com/mtgox?Currency=%s' % (",".join(currencies))
        WebSocketClientBase.__init__(self, url)
        self.__nonce = base.Nonce()
        self.__apiKey = apiKey
        self.__apiSecret = apiSecret
        self.__ignoreMultiCurrency = ignoreMultiCurrency
        self.__publicTradeChannel = PublicChannels.getTradeChannel()

    def authCall(self, call, params={}, item="BTC", currency=""):
        # https://en.bitcoin.it/wiki/MtGox/API/Streaming#Authenticated_commands
        # If 'Invalid call' remark is received, this is probably due to a bad nonce.
        nonce = self.__nonce.next()
        requestId = get_hex_md5(str(nonce))
        requestDict = {
            "id": requestId,
            "call": call,
            "nonce": nonce,
            "params": params,
            "item": item,
            "currency": currency,
            }
        request = json.dumps(requestDict)

        # https://en.bitcoin.it/wiki/MtGox/API/HTTP
        binaryKey = apikey_as_binary(self.__apiKey)
        signature = sign_request(request, self.__apiSecret)
        callDict = {
            "op": "call",
            "id": requestId,
            "call": base64.b64encode(binaryKey + signature + request),
            "context": "mtgox.com"}
        msg = json.dumps(callDict)
        self.send(msg, False)
        return requestId

    def onMessage(self, data):
        if data["op"] == "private":
            self.onPrivate(data)
        elif data["op"] == "subscribe":
            self.onSubscribe(data)
        elif data["op"] == "unsubscribe":
            self.onUnsubscribe(data)
        elif data["op"] == "remark":
            self.onRemark(data)
        elif data["op"] == "result":
            self.onResult(data)
        else:
            self.onUnknownOperation(data["op"], data)

    def subscribePrivateChannel(self, privateKeyId):
        msg = json.dumps({"op": "mtgox.subscribe", "key": privateKeyId})
        self.send(msg, False)

    def subscribeChannel(self, channelId):
        msg = json.dumps({"op": "subscribe", "channel": channelId})
        self.send(msg, False)

    def unsubscribeChannel(self, channelId):
        msg = json.dumps({"op": "unsubscribe", "channel": channelId})
        self.send(msg, False)

#    def createOrder(self, orderType, amount, currency):
#        return self.authCall("order/add", {"type":orderType, "amount":amount}, currency=currency)

    def requestPrivateIdKey(self):
        return self.authCall("private/idkey")

    def onPrivate(self, data):
        if data["private"] == "ticker":
            self.onTicker(base.Ticker(data["ticker"]))
        elif data["private"] == "trade":
            # From https://en.bitcoin.it/wiki/MtGox/API/HTTP/v1:
            # A trade can appear in more than one currency, to ignore duplicates,
            # use only the trades having primary =Y
            if not self.__ignoreMultiCurrency or data["trade"]["primary"] == "Y":
                self.onTrade(base.Trade(data["trade"]), data["channel"] == self.__publicTradeChannel)
        elif data["private"] == "wallet":
            self.onWallet(base.Wallet(data["wallet"]))
        elif data["private"] == "depth":
            self.onDepth(base.Depth(data["depth"]))
        elif data["private"] == "user_order":
            self.onUserOrder(base.UserOrder(data["user_order"]))
        elif data["private"] == "result":
            print "----"
            print data
            print "----"
            pass

    def onSubscribe(self, data):
        pass

    def onUnsubscribe(self, data):
        pass

    def onRemark(self, data):
        pass

    def onResult(self, data):
        pass

    def onUnknownOperation(self, operation, data):
        pass

    def onTicker(self, ticker):
        pass

    def onTrade(self, trade, publicChannel):
        pass

    def onWallet(self, wallet):
        pass

    def onDepth(self, depth):
        pass

    def onUserOrder(self, userOrder):
        pass
