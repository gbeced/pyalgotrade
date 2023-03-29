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
.. moduleauthor:: Robert Lee
    Splits out LiveFeed to allow for both live bar feeds and live trade feeds.

"""

import abc
import datetime
import time
import queue
import threading
import asyncio
from alpaca_trade_api.entity import Quote

import zmq
import json
import pandas as pd

from pyalgotrade import feed
from pyalgotrade import dataseries
from pyalgotrade import bar, quote, trade

from pyalgotrade.dataseries import bards, tradeds, quoteds
from pyalgotrade.alpaca import common


class LiveFeed(threading.Thread):
    """A thread that takes incoming messages from Alapaca and publishes them on ZMQ sockets.
    """

    def __init__(self, publishing_address = 'tcp://*:34567', api_key_id = None, api_secret_key = None):
        
        # Create sockets
        self.__zmq_context = zmq.Context()

        # for publishing data from the websocket
        # (from Alpaca's stream.TradingStream and stream.DataStream)
        self._publishing_address = publishing_address
        self.__socket = self.__zmq_context.socket(zmq.PUB)
        self.__socket.bind(self._publishing_address)
        common.logger.info(
            f'Live feed publishing data at {self._publishing_address}'
            )
        
        # threading stuff
        self.__stop = False
        self.__stopped = False

        # make connection
        # use the non-paper connection to get data
        self.stream = common.make_connection(
            connection_type = 'stream', api_key_id = api_key_id, api_secret_key = api_secret_key, live = True)
        
    
    def start(self):
        self.stream.run()
    
    def stop(self):
        self.__zmq_context.term()


    # for dynamic subscription
    # See https://github.com/alpacahq/alpaca-trade-api-python/blob/master/examples/websockets/dynamic_subscription_example.py
    # def consumer_thread():
    #     try:
    #         # make sure we have an event loop, if not create a new one
    #         loop = asyncio.get_event_loop()
    #         loop.set_debug(True)
    #     except RuntimeError:
    #         asyncio.set_event_loop(asyncio.new_event_loop())


    # Functions to handle incoming messages
    async def publish(self, topic, messages):
        for message in messages:
            self.__socket.send_multipart([topic.encode(), message])
    
    def publish_with_topic(self, topic):
        async def publish(message):
            msg = json.dumps(message, default = common.json_serializer)
            self.__socket.send_multipart([topic.encode(), msg.encode()])
        return publish
        # async def print_stuff(message):
        #     print(pd.to_datetime(message['t'].to_unix_nano()))
        # return print_stuff

    # subscribe to real time data
    def subscribe_trade_updates(self):
        self.stream.subscribe_trade_updates(self.publish_with_topic('BROKER'))
    
    def subscribe_trades(self, *symbols, handler_cancel_errors = None, handler_corrections = None):
        self.stream.subscribe_trades(self.publish_with_topic('TRADES'), *symbols, handler_cancel_errors, handler_corrections)

    def subscribe_quotes(self, *symbols):
        self.stream.subscribe_quotes(self.publish_with_topic('QUOTES'), *symbols)    

    def subscribe_bars(self, *symbols):
        self.stream.subscribe_bars(self.publish_with_topic('BARS'), *symbols)
    
    def subscribe_dailiy_bars(self, *symbols):
        self.stream.subscribe_daily_bars(self.publish_with_topic('BARS'), *symbols)

    def subscribe_statuses(self, *symbols):
        self.stream.subscribe_statuses(self.publish_with_topic('STATUSES'), *symbols)

    def subscribe_lulds(self, *symbols):
        self.stream.subscribe_lulds(self.publish_with_topic('LULDS'), *symbols)
    
    def subscribe_crypto_trades(self, *symbols):
        # self.stream.subscribe_crypto_trades(self.publish_with_topic('TRADES'), symbols)
        self.stream.subscribe_crypto_trades(self.publish_with_topic('TRADES'), *symbols)

    def subscribe_crypto_quotes(self, *symbols):
        self.stream.subscribe_crypto_quotes(self.publish_with_topic('QUOTES'), *symbols)

    def subscribe_crypto_bars(self, *symbols):
        self.stream.subscribe_crypto_bars(self.publish_with_topic('BARS'), *symbols)

    def subscribe_crypto_daily_bars(self, *symbols):
        self.stream.subscribe_crypto_daily_bars(self.publish_with_topic('BARS'), *symbols)

class EventQueuer(threading.Thread):
    """A thread that checks a ZMQ SUB socket for streaming data.
    """    
    POLL_FREQUENCY = 0.5

    def __init__(self, liveFeedAddress = 'tcp://localhost:34567', topic = ''):
        super(EventQueuer, self).__init__()
        
        self.__zmq_context = zmq.Context()
        self.__event_socket = self.__zmq_context.socket(zmq.SUB)
        self.__event_socket.setsockopt(zmq.SUBSCRIBE, str(topic).encode())
        self.__event_socket.connect(liveFeedAddress)
        self.__queue = queue.Queue()
        self.__stop = False

    def _getNewEvent(self):
        try:
            topic, update = self.__event_socket.recv_multipart(zmq.NOBLOCK)
            update = update.decode()
            update = json.loads(update, object_hook = common.json_deserializer)
            return update
        except zmq.ZMQError as exc:
            if exc.errno == zmq.EAGAIN:
                # nothing to get
                return
            else:
                raise

    def getQueue(self):
        return self.__queue

    def start(self):
        if (newEvent:= self._getNewEvent()):
            self.__queue.put(newEvent)
            # common.logger.info(f'New Event: {newEvent}')
        super(EventQueuer, self).start()

    def run(self):
        while not self.__stop:
            try:
                if (newEvent:= self._getNewEvent()):
                    self.__queue.put(newEvent)
                    # common.logger.info(f'New Event: {newEvent}')
                else:
                    time.sleep(EventQueuer.POLL_FREQUENCY)
            except Exception as e:
                common.logger.critical("Error retrieving new events", exc_info=e)

    def stop(self):
        self.__stop = True

class BaseLiveDataFeed(feed.BaseFeed):
    
    QUEUE_TIMEOUT = 0.01

    def __init__(self, liveFeedAddress, topic, maxLen = None):
        super(BaseLiveDataFeed, self).__init__(maxLen)
        
        # Queue to get data from
        self.__dataQueuer = EventQueuer(liveFeedAddress, topic)

        # keep track of most recent data
        self.__currentData = None
        self.__lastData = None
    
    # BEGIN feed.BaseFeed interface
    def reset(self):
        self.__currentData = None
        self.__lastData = {}
        super(BaseLiveDataFeed, self).reset()
    
    @abc.abstractmethod
    def createDataSeries(self, key, maxLen):
        pass
    
    def getNextValues(self):
        # from barfeed.BaseBarFeed.getNextValues
        dateTime = None
        data = self.getNextData()
        if data is not None:
            dateTime = data.getDateTime
        
        self.__currentData = data
        for instrument in data.getInstruments():
            self.__lastData[instrument] = data[instrument]

        return (dateTime, data)

    # END feed.BaseFeed interface

    def getNextData(self):
        ret = None
        try:
            ret = self.__dataQueuer.getQueue().get(block = True, timeout = BaseLiveDataFeed.QUEUE_TIMEOUT)
            return ret
        except:
            return False

class LiveBarFeed(BaseLiveDataFeed):
    def __init__(self, liveFeedAddress, maxLen = None):
        super(LiveBarFeed, self).__init__(liveFeedAddress, 'BARS')
    
    def createDataSeries(self, key, maxLen):
        ret = bards.BarDataSeries(maxLen)
        # real time objects do not use adjusted values
        ret.setUseAdjustedValues(False)
        return ret

class LiveTradeFeed(BaseLiveDataFeed):
    def __init__(self, liveFeedAddress, maxLen = None):
        super(LiveBarFeed, self).__init__(liveFeedAddress, 'TRADES')
    
    def createDataSeries(self, key, maxLen):
        ret = tradeds.TradeDataSeries(maxLen)
        return ret

class LiveQuoteFeed(BaseLiveDataFeed):
    def __init__(self, liveFeedAddress, maxLen = None):
        super(LiveBarFeed, self).__init__(liveFeedAddress, 'QUOTES')
    
    def createDataSeries(self, key, maxLen):
        ret = quoteds.QuoteDataSeries(maxLen)
        return ret

def fromAlpacaData(alpacaDataPoint):
    # see https://alpaca.markets/docs/api-documentation/api-v2/market-data/alpaca-data-api-v2/real-time/
    # bars
    if alpacaDataPoint['T'] == 'b':
        data = bar.Bar(
            dateTime = alpacaDataPoint.get('t'),
            open_ = alpacaDataPoint.get('o'),
            high = alpacaDataPoint.get('h'),
            low = alpacaDataPoint.get('l'),
            close = alpacaDataPoint.get('c'),
            volume = alpacaDataPoint.get('v'),
            adjClose = alpacaDataPoint.get('c'),
            frequency = None,
            extra = {'symbol': alpacaDataPoint.get('S')}
        )
    # trades
    elif alpacaDataPoint.get('T') == 't':
        data = trade.Trade(
            dateTime = alpacaDataPoint.get('t'),
            tradeId = alpacaDataPoint.get('i'),
            price = alpacaDataPoint.get('p'),
            size = alpacaDataPoint.get('s'),
            exchange = alpacaDataPoint.get('x'),
            condition = alpacaDataPoint.get('c'),
            tape = alpacaDataPoint.get('z'),
            takerSide = alpacaDataPoint.get('tks'),
            extra = {'symbol': alpacaDataPoint.get('S')}
        )
    # quotes
    elif alpacaDataPoint.get('T') == 'q':
        data = quote.Quote(
            dateTime = alpacaDataPoint.get('t'),
            askExchange = alpacaDataPoint.get('ax'),
            askPrice = alpacaDataPoint.get('ap'),
            askSize = alpacaDataPoint.get('as'),
            bidExchange = alpacaDataPoint.get('bx'),
            bidPrice = alpacaDataPoint.get('bp'),
            bidSize = alpacaDataPoint.get('bs'),
            condition = alpacaDataPoint.get('c'),
            tape = alpacaDataPoint.get('z'),
            extra = {'symbol': alpacaDataPoint.get('S')}
        )
    
    return data

