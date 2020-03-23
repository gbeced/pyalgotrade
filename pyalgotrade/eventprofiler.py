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
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import numpy as np
from six.moves import xrange

from pyalgotrade.technical import roc
from pyalgotrade import dispatcher
from pyalgotrade.bar import pair_to_key


class Results(object):
    """Results from the profiler."""
    def __init__(self, eventsDict, lookBack, lookForward):
        assert(lookBack > 0)
        assert(lookForward > 0)
        self.__lookBack = lookBack
        self.__lookForward = lookForward
        self.__values = [[] for i in xrange(lookBack+lookForward+1)]
        self.__eventCount = 0

        # Process events.
        for instrument, events in eventsDict.items():
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

    def eventOccurred(self, instrument, priceCurrency, barDS):
        """Override (**mandatory**) to determine if an event took place in the last bar (barDS[-1]).

        :param instrument: Instrument identifier.
        :type instrument: string.
        :param priceCurrency: Price currency.
        :type priceCurrency: string.
        :param barDS: The BarDataSeries for the given instrument and price currency.
        :type barDS: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
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

    def __addPastReturns(self, instrument, priceCurrency, event):
        key = pair_to_key(instrument, priceCurrency)
        begin = (event.getLookBack() + 1) * -1
        for t in xrange(begin, 0):
            try:
                ret = self.__rets[key][t]
                if ret is not None:
                    event.setValue(t+1, ret)
            except IndexError:
                pass

    def __addCurrentReturns(self, instrument, priceCurrency):
        nextTs = []
        key = pair_to_key(instrument, priceCurrency)
        for event, t in self.__futureRets[key]:
            event.setValue(t, self.__rets[key][-1])
            if t < event.getLookForward():
                t += 1
                nextTs.append((event, t))
        self.__futureRets[key] = nextTs

    def __onBars(self, dateTime, bars):
        for bar in bars.getBars():
            instrument = bar.getInstrument()
            priceCurrency = bar.getPriceCurrency()
            key = pair_to_key(instrument, priceCurrency)
            barDS = self.__feed.getDataSeries(instrument, priceCurrency)

            self.__addCurrentReturns(instrument, priceCurrency)
            eventOccurred = self.__predicate.eventOccurred(instrument, priceCurrency, barDS)
            if eventOccurred:
                event = Event(self.__lookBack, self.__lookForward)
                self.__events[key].append(event)
                self.__addPastReturns(instrument, priceCurrency, event)
                # Add next return for this instrument at t=1.
                self.__futureRets[key].append((event, 1))

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

            # for instrument in feed.getRegisteredInstruments():
            for barDS in feed.getAllDataSeries():
                key = pair_to_key(barDS.getInstrument(), barDS.getPriceCurrency())
                self.__events.setdefault(key, [])
                self.__futureRets[key] = []
                if useAdjustedCloseForReturns:
                    ds = barDS.getAdjCloseDataSeries()
                else:
                    ds = barDS.getCloseDataSeries()
                self.__rets[key] = roc.RateOfChange(ds, 1)

            feed.getNewValuesEvent().subscribe(self.__onBars)
            disp = dispatcher.Dispatcher()
            disp.addSubject(feed)
            disp.run()
        finally:
            feed.getNewValuesEvent().unsubscribe(self.__onBars)


def build_plot(profilerResults):
    import matplotlib.pyplot as plt

    # Calculate each value.
    x = []
    mean = []
    std = []
    for t in xrange(profilerResults.getLookBack()*-1, profilerResults.getLookForward()+1):
        x.append(t)
        values = np.asarray(profilerResults.getValues(t))
        mean.append(values.mean())
        std.append(values.std())

    # Cleanup
    plt.clf()
    # Plot a line with the mean cumulative returns.
    plt.plot(x, mean, color='#0000FF')

    # Error bars starting on the first lookforward period.
    lookBack = profilerResults.getLookBack()
    firstLookForward = lookBack+1
    plt.errorbar(
        x=x[firstLookForward:], y=mean[firstLookForward:], yerr=std[firstLookForward:],
        capsize=3,
        ecolor='#AAAAFF', alpha=0.5
    )

    # Horizontal line at the level of the first cumulative return.
    plt.axhline(
        y=mean[lookBack],
        xmin=-1*profilerResults.getLookBack(), xmax=profilerResults.getLookForward(),
        color='#000000'
    )

    plt.xlim(profilerResults.getLookBack()*-1-0.5, profilerResults.getLookForward()+0.5)
    plt.xlabel('Time')
    plt.ylabel('Cumulative returns')


def plot(profilerResults):
    """Plots the result of the analysis.

    :param profilerResults: The result of the analysis
    :type profilerResults: :class:`Results`.
    """

    import matplotlib.pyplot as plt

    build_plot(profilerResults)
    plt.show()
