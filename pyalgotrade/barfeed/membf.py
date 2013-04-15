# PyAlgoTrade
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
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

from pyalgotrade import barfeed
from pyalgotrade.barfeed import helpers

# This class is responsible for:
# - Holding bars in memory.
# - Aligning them with respect to time.
#
# Subclasses should:
# - Forward the call to start() if they override it.

class Feed(barfeed.BarFeed):
	def __init__(self, frequency):
		barfeed.BarFeed.__init__(self, frequency)
		self.__bars = {}
		self.__nextBarIdx = {}
		self.__started = False
		self.__barsLeft = 0

	def start(self):
		self.__started = True
		# Set session close attributes to bars.
		for instrument, bars in self.__bars.iteritems():
			helpers.set_session_close_attributes(bars)
			self.__barsLeft = max(self.__barsLeft, len(bars))

	def stop(self):
		pass

	def join(self):
		pass

	def addBarsFromSequence(self, instrument, bars):
		if self.__started:
			raise Exception("Can't add more bars once you started consuming bars")

		self.__bars.setdefault(instrument, [])
		self.__nextBarIdx.setdefault(instrument, 0)

		# Add and sort the bars
		self.__bars[instrument].extend(bars)
		barCmp = lambda x, y: cmp(x.getDateTime(), y.getDateTime())
		self.__bars[instrument].sort(barCmp)

		self.registerInstrument(instrument)

	def stopDispatching(self):
		ret = True
		# Check if there is at least one more bar to return.
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars):
				ret = False
				break
		return ret

	def fetchNextBars(self):
		# All bars must have the same datetime. We will return all the ones with the smallest datetime.
		smallestDateTime = None

		# Make a first pass to get the smallest datetime.
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars):
				if smallestDateTime == None or bars[nextIdx].getDateTime() < smallestDateTime:
					smallestDateTime = bars[nextIdx].getDateTime()

		if smallestDateTime == None:
			assert(self.__barsLeft == 0)
			return None

		# Make a second pass to get all the bars that had the smallest datetime.
		ret = {}
		for instrument, bars in self.__bars.iteritems():
			nextIdx = self.__nextBarIdx[instrument]
			if nextIdx < len(bars) and bars[nextIdx].getDateTime() == smallestDateTime:
				ret[instrument] = bars[nextIdx]
				self.__nextBarIdx[instrument] += 1

		self.__barsLeft -= 1
		return ret

	def getBarsLeft(self):
		return self.__barsLeft

	def loadAll(self):
		self.start()
		for b in self:
			pass
		self.stop()
		self.join()

