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

import numpy as np
import matplotlib.pyplot as plt

from pyalgotrade.technical import roc
from pyalgotrade import dispatcher


class Results(object):
    """Results from the profiler."""
    def __init__(self, eventsDict, lookBack, lookForward):
        assert(lookBack > 0)
        assert(lookForward > 0)
        self.__lookBack = lookBack
        self.__lookForward = lookForward
        self.__values = [[] for i in range(lookBack+lookForward+1)]
        self.__eventCount = 0

        # Process events.
        for instrument, events in list(eventsDict.items()):
            for event in events:
                # Skip events which are on the boundary or for some reason are not complete.
                if event.isComplete():
                    self.__eventCount += 1
                    # Compute cumulative returns: (1 + R1)*(1 + R2)*...*(1 + Rn)
                    values = np.cumprod(event.getValues() + 1)
                    # Normalize everything to the time of the event
                    values = values / values[event.getLookBack()]
                    for t in range(event.getLookBack()*-1, event.getLookForward()+1):
                        self.setValue(t, values[t+event.getLookBack()])

    def __mapPos(self, t):
        assert(t >= -1*self.__lookBack and t <= self.__lookForward)
        return t + self.__lookBack

    def setValue(self, t, value):
        if value is None:
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

    def getEventCount(self):
        """Returns the number of events occurred. Events that are on the boundary are skipped."""
        return self.__eventCount


class Predicate(object):
    """Base class for event identification. You should subclass this to implement
    the event identification logic."""

    def eventOccurred(self, instrument, bards):
        """Override (**mandatory**) to determine if an event took place in the last bar (bards[-1]).

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param bards: The BarDataSeries for the given instrument.
        :type bards: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
        :rtype: boolean.
        """
        raise NotImplementedError()


class Event(object):
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

    def isComplete(self):
        return not any(np.isnan(self.__values))

    def getLookBack(self):
        return self.__lookBack

    def getLookForward(self):
        return self.__lookForward

    def setValue(self, t, value):
        if value is not None:
            pos = self.__mapPos(t)
            self.__values[pos] = value

    def getValue(self, t):
        pos = self.__mapPos(t)
        return self.__values[pos]

    def getValues(self):
        return self.__values


class Profiler(object):
    """This class is responsible for scanning over historical data and analyzing returns before
    and after the events.

    :param predicate: A :class:`Predicate` subclass responsible for identifying events.
    :type predicate: :class:`Predicate`.
    :param lookBack: The number of bars before the event to analyze. Must be > 0.
    :type lookBack: int.
    :param lookForward: The number of bars after the event to analyze. Must be > 0.
    :type lookForward: int.
    """

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
        for t in range(begin, 0):
            try:
                ret = self.__rets[instrument][t]
                if ret is not None:
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

    def __onBars(self, dateTime, bars):
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
        """Returns the results of the analysis.

        :rtype: :class:`Results`.
        """
        return Results(self.__events, self.__lookBack, self.__lookForward)

    def run(self, feed, useAdjustedCloseForReturns=True):
        """Runs the analysis using the bars supplied by the feed.

        :param barFeed: The bar feed to use to run the analysis.
        :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
        :param useAdjustedCloseForReturns: True if adjusted close values should be used to calculate returns.
        :type useAdjustedCloseForReturns: boolean.
        """

        if useAdjustedCloseForReturns:
            assert feed.barsHaveAdjClose(), "Feed doesn't have adjusted close values"

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

            feed.getNewValuesEvent().subscribe(self.__onBars)
            disp = dispatcher.Dispatcher()
            disp.addSubject(feed)
            disp.run()
        finally:
            feed.getNewValuesEvent().unsubscribe(self.__onBars)


def build_plot(profilerResults):
    # Calculate each value.
    x = []
    y = []
    std = []
    for t in range(profilerResults.getLookBack()*-1, profilerResults.getLookForward()+1):
        x.append(t)
        values = np.asarray(profilerResults.getValues(t))
        y.append(values.mean())
        std.append(values.std())

    # Plot
    plt.clf()
    plt.plot(x, y, color='#0000FF')
    eventT = profilerResults.getLookBack()
    # stdBegin = eventT + 1
    # plt.errorbar(x[stdBegin:], y[stdBegin:], std[stdBegin:], alpha=0, ecolor='#AAAAFF')
    plt.errorbar(x[eventT+1:], y[eventT+1:], std[eventT+1:], alpha=0, ecolor='#AAAAFF')
    # plt.errorbar(x, y, std, alpha=0, ecolor='#AAAAFF')
    plt.axhline(y=y[eventT], xmin=-1*profilerResults.getLookBack(), xmax=profilerResults.getLookForward(), color='#000000')
    plt.xlim(profilerResults.getLookBack()*-1-0.5, profilerResults.getLookForward()+0.5)
    plt.xlabel('Time')
    plt.ylabel('Cumulative returns')


def plot(profilerResults):
    """Plots the result of the analysis.

    :param profilerResults: The result of the analysis
    :type profilerResults: :class:`Results`.
    """

    build_plot(profilerResults)
    plt.show()
