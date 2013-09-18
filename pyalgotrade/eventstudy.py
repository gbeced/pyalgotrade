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

import numpy as np
import matplotlib.pyplot as plt

from pyalgotrade.technical import roc
from pyalgotrade import observer

class Results:
	def __init__(self, lookBack, lookForward):
		assert(lookBack > 0)
		assert(lookForward > 0)
		self.__lookBack = lookBack
		self.__lookForward = lookForward
		self.__values = [[] for i in xrange(lookBack+lookForward+1)]

	def __mapPos(self, t):
		assert(t >= -1*self.__lookBack and t <= self.__lookForward)
		return t + self.__lookBack

	def setValue(self, t, value):
		if value == None:
			raise Exception("Invalid value at time %d" % (t))
		pos = self.__mapPos(t)
		self.__values[pos].append(value)

	def getValues(self, t):
		pos = self.__mapPos(t)
		return self.__values[pos]

	def getLookBack(self):
		return self.__lookBack

	def getLookForward(self):
		return self.__lookForward

class Predicate:
	def eventOccurred(self, instrument, bards):
		raise NotImplementedError()

class Event:
	def __init__(self, lookBack, lookForward):
		assert(lookBack > 0)
		assert(lookForward > 0)
		self.__lookBack = lookBack
		self.__lookForward = lookForward
		self.__values = np.empty((lookBack + lookForward + 1))
		self.__values[:] = np.NAN

	def __mapPos(self, t):
		assert(t >= -1*self.__lookBack and t <= self.__lookForward)
		return t + self.__lookBack

	def onBoundary(self):
		return any(np.isnan(self.__values))

	def getLookBack(self):
		return self.__lookBack

	def getLookForward(self):
		return self.__lookForward

	def setValue(self, t, value):
		if value == None:
			raise Exception("Invalid value at time %d" % (t))
		pos = self.__mapPos(t)
		self.__values[pos] = value

	def getValue(self, t):
		pos = self.__mapPos(t)
		return self.__values[pos]

	def getValues(self):
		return self.__values

class Profiler:
	def __init__(self, predicate, lookBack, lookForward):
		assert(lookBack > 0)
		assert(lookForward > 0)
		self.__predicate = predicate
		self.__lookBack = lookBack
		self.__lookForward = lookForward
		self.__feed = None
		self.__rets = {}
		self.__futureRets = {}
		self.__events = {}

	def __addPastReturns(self, instrument, event):
		begin = (event.getLookBack() + 1) * -1
		for t in xrange(begin, 0):
			try:
				ret = self.__rets[instrument][t]
				if ret != None:
					event.setValue(t+1, ret)
			except IndexError:
				pass

	def __addCurrentReturns(self, instrument):
		nextTs = []
		for event, t in self.__futureRets[instrument]:
			event.setValue(t, self.__rets[instrument][-1])
			if t < event.getLookForward():
				t += 1
				nextTs.append((event, t))
		self.__futureRets[instrument] = nextTs

	def __onBars(self, bars):
		for instrument in bars.getInstruments():
			self.__addCurrentReturns(instrument)
			eventOccurred = self.__predicate.eventOccurred(instrument, self.__feed[instrument])
			if eventOccurred:
				event = Event(self.__lookBack, self.__lookForward)
				self.__events[instrument].append(event)
				self.__addPastReturns(instrument, event)
				# Add next return for this instrument at t=1.
				self.__futureRets[instrument].append((event, 1))

	def getResults(self):
		ret = Results(self.__lookBack, self.__lookForward)
		for instrument, events in self.__events.items():
			for event in events:
				# Skip events which are on the boundary.
				if not event.onBoundary():
					# Compute cumulative returns: (1 + R1)*(1 + R2)*...*(1 + Rn)
					values = np.cumprod(event.getValues() + 1)
					# Normalize everything to the time of the event
					values = values / values[event.getLookBack()]
					for t in range(event.getLookBack()*-1, event.getLookForward()+1):
						ret.setValue(t, values[t+event.getLookBack()])
		return ret

	def run(self, feed, useAdjustedCloseForReturns=True):
		try:
			self.__feed = feed
			self.__rets = {}
			self.__futureRets = {}
			for instrument in feed.getRegisteredInstruments():
				self.__events.setdefault(instrument, [])
				self.__futureRets[instrument] = []
				if useAdjustedCloseForReturns:
					ds = feed[instrument].getAdjCloseDataSeries()
				else:
					ds = feed[instrument].getCloseDataSeries()
				self.__rets[instrument] = roc.RateOfChange(ds, 1)

			feed.getNewBarsEvent().subscribe(self.__onBars)
			dispatcher = observer.Dispatcher()
			dispatcher.addSubject(feed)
			dispatcher.run()
		finally:
			feed.getNewBarsEvent().unsubscribe(self.__onBars)

def build_plot(eventResults):
	# Calculate each value.
	x = []
	y = []
	std = []
	for t in xrange(eventResults.getLookBack()*-1, eventResults.getLookForward()+1):
		x.append(t)
		values = np.array(eventResults.getValues(t))
		# This will fail if we don't have the same number of values on each window
		# values = np.array(eventResults.getValues(0)) / np.array(eventResults.getValues(t))
		y.append(values.mean())
		std.append(values.std())

	# Plot
	plt.clf()
	plt.plot(x, y, color='#0000FF')
	eventT = eventResults.getLookBack()
	# stdBegin = eventT + 1
	# plt.errorbar(x[stdBegin:], y[stdBegin:], std[stdBegin:], alpha=0, ecolor='#AAAAFF')
	plt.errorbar(x[eventT+1:], y[eventT+1:], std[eventT+1:], alpha=0, ecolor='#AAAAFF')
	# plt.errorbar(x, y, std, alpha=0, ecolor='#AAAAFF')
	plt.axhline(y=y[eventT],xmin=-1*eventResults.getLookBack(), xmax=eventResults.getLookForward(), color='#000000')
	plt.xlim(eventResults.getLookBack()*-1-0.5, eventResults.getLookForward()+0.5)
	plt.xlabel('Time')
	plt.ylabel('Cumulative returns')

def plot(eventResults):
	build_plot(eventResults)
	plt.show()

