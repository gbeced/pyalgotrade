# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import barfeed
from pyalgotrade import bar

class BarFeed(barfeed.BarFeed):
	def __init__(self, currencies, maxLen=None):
		barfeed.BarFeed.__init__(self, barfeed.Frequency.REALTIME, maxLen)
		self.__barDicts = []
		for currency in currencies:
			self.registerInstrument(currency)

	def addTrade(self, trade):
		if trade.getCurrency() in self.getRegisteredInstruments():
			# Build a bar for each trade.
			# We're using getDateTimeWithMicroseconds instead of getDateTime because sometimes there are many
			# trades in the same second and that produces errors in:
			# - barfeed.BarFeed.getNextBars and in 
			# - dataseries.SequenceDataSeries.appendWithDateTime
			barDict = {
					trade.getCurrency() : bar.Bar(trade.getDateTimeWithMicroseconds(), trade.getPrice(), trade.getPrice(), trade.getPrice(), trade.getPrice(), trade.getAmount(), trade.getPrice())
					}
			self.__barDicts.append(barDict)

	def fetchNextBars(self):
		ret = None
		if len(self.__barDicts):
			ret = self.__barDicts.pop(0)
		return ret

	def peekDateTime(self):
		return False

	def eof(self):
		return len(self.__barDicts) == 0

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

