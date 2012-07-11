# PyAlgoTrade
# 
# Related materials
# Interactive Brokers API:  http://www.interactivebrokers.com/en/software/api/api.htm
# IbPy: http://code.google.com/p/ibpy/ 
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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
.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""

from pyalgotrade import bar

class Bar(bar.Bar):
	"""An instrument's prices at a given time.
        :param instrument: Instrument's symbol
        :type instrument: str
	:param dateTime: The date time.
	:type dateTime: datetime.datetime
	:param open_: The opening price.
	:type open_: float
	:param high: The highest price.
	:type high: float
	:param low: The lowest price.
	:type low: float
	:param close: The closing price.
	:type close: float
	:param volume: The volume.
	:type volume: float
	:param vwap: Volume weighted average price (IB specific)
	:type vwap: float
	:param tradeCount: Number of trades (IB specific)
	:type tradeCount: int
	"""
	def __init__(self, instrument, dateTime, open_, high, low, close, volume, vwap, tradeCount):
                bar.Bar.__init__(self, dateTime, open_, high, low, close, volume, adjClose=None)

                self.__instrument = instrument
                self.__vwap = vwap
                self.__tradeCount = tradeCount

        def getInstrument(self):
                """Returns the instrument's symbol."""
                return self.__instrument

        def getVWAP(self):
                """Returns the Volume Weighted Average Price."""
                return self.__vwap

        def getTradeCount(self):
                """Returns the trade count."""
                return self.__tradeCount


        def __repr__(self):
                return str("%s - %s: open=%.2f, high=%.2f, low=%.2f, close=%.2f, volume=%d, vwap=%.2f, tradeCount=%d" %
                            (self.getDateTime(), self.getInstrument(), self.getOpen(), self.getHigh(), self.getLow(), self.getClose(),
                             self.getVolume(), self.getVWAP(), self.getTradeCount()))
    

