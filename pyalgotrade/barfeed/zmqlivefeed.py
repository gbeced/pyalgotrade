"""
.. moduleauthor:: Massimo Fierro <massimo.fierro@ghrholdings.com>m>
"""

import datetime

from uuid import uuid4
from random import randint
from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade.zmq.zmqclient import ZmqClientThread


class TickBar(bar.Bar):
    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__price', '__volume', '__buySide')

    def __init__(self, dateTime, price, volume, buyside):
        self.__dateTime = dateTime
        self.__price = price  # trade.getPrice()
        self.__volume = volume  # trade.getAmount()
        self.__buySide = buyside  # trade.isBuy()
        self.__stopped = True

    def setUseAdjustedValue(self, useAdjusted):
        if useAdjusted:
            raise Exception("Adjusted close is not available")

    def getFrequency(self):
        return bar.Frequency.TRADE

    def getDateTime(self):
        return self.__dateTime

    def getOpen(self, adjusted=False):
        return self.__price

    def getHigh(self, adjusted=False):
        return self.__price

    def getLow(self, adjusted=False):
        return self.__price

    def getClose(self, adjusted=False):
        return self.__price

    def getVolume(self):
        return self.__volume

    def getAdjClose(self):
        return None

    def getTypicalPrice(self):
        return self.__price

    def getPrice(self):
        return self.__price

    def getUseAdjValue(self):
        return False

    def isBuy(self):
        return self.__buySide

    def isSell(self):
        return not self.__buySide


class ZmqLiveFeed(barfeed.BaseBarFeed):
    """A real-time BarFeed that builds bars from live trades using a
        ZeroMQ PUB provider.

    :param maxLen: The maximum number of values that the
        :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a
        corresponding number of items are discarded from the opposite end.
        If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, address, port, frequency=bar.Frequency.TRADE,
                 maxLen=None):
        super(ZmqLiveFeed, self).__init__(frequency, maxLen)
        self.__bars = []
        self.__frequency = frequency
        self.__useAdjustedValues = False
        self.__defaultInstrument = None
        self.__client = ZmqClientThread("tcp://{!s}:{!s}".format(
            address, port
        ))
        self.__client.setRecvCallback(self.onReceive)
        self.__client.setIdleCallback(self.onIdle)
        self.__dispatched = False

    def onIdle(self):
        self.__dispatched = False

    def onReceive(self, timestamp, instrument, o, h, l, c, vol):
        self.__dispatched = True
        self.__bars.append({
            instrument: TickBar(datetime(timestamp), o, h, l, c, vol)
        })

    # Return the datetime for the current bars.
    def getCurrentDateTime(self):
        '''Live feed, hence datetime.now()'''
        return datetime.datetime.now()

    # Return True if bars provided have adjusted close values.
    def barsHaveAdjClose(self):
        '''Live feed, hence False'''
        return False

    def getNextBars(self):
        ret = None
        try:
            ret = bar.Bars(self.__bars.pop(0))
        except:
            pass
        return ret

    def start(self):
        # print "DEBUG: GmassLiveFeed.start()"
        self.__client.start()
        self.__stopped = False

    def stop(self):
        # print "DEBUG: GmassLiveFeed.stop()"
        self.__client.stop()
        self.__stopped = True

    def eof(self):
        return self.__stopped

    def peekDateTime(self):
        ret = None
        try:
            bars = self.__bars[0]
            ret = bars.getDateTime()
        except Exception as ex:
            pass
        return ret

    def join(self):
        self.__client.join()

    def dispatch(self):
        # Note that we may return True even if we didn't dispatch any Bar
        # event.
        ret = False
        if self.__dispatched:
            ret = True
        if super(ZmqLiveFeed, self).dispatch():
            ret = True
        return ret
