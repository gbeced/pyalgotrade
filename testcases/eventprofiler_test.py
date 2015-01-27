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

import datetime

import common

from pyalgotrade import eventprofiler
from pyalgotrade.barfeed import yahoofeed


class Predicate(eventprofiler.Predicate):
    def __init__(self, eventDates):
        self.__dates = eventDates

    def eventOccurred(self, instrument, bards):
        ret = False
        if bards[-1].getDateTime().date() in self.__dates:
            ret = True
        return ret


class EventProfilerTestCase(common.TestCase):
    def testNoEvents(self):
        feed = yahoofeed.Feed()
        feed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2000-yahoofinance.csv"))

        predicate = Predicate([])
        eventProfiler = eventprofiler.Profiler(predicate, 5, 5)
        eventProfiler.run(feed, True)
        self.assertEqual(eventProfiler.getResults().getEventCount(), 0)

    def testEventsOnBoundary(self):
        feed = yahoofeed.Feed()
        feed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2000-yahoofinance.csv"))

        dates = []
        dates.append(datetime.date(2000, 1, 3))
        dates.append(datetime.date(2000, 1, 4))
        dates.append(datetime.date(2000, 1, 5))
        dates.append(datetime.date(2000, 1, 6))
        dates.append(datetime.date(2000, 1, 7))
        dates.append(datetime.date(2000, 1, 10))
        dates.append(datetime.date(2000, 12, 22))
        dates.append(datetime.date(2000, 12, 26))
        dates.append(datetime.date(2000, 12, 27))
        dates.append(datetime.date(2000, 12, 28))
        dates.append(datetime.date(2000, 12, 29))
        predicate = Predicate(dates)
        eventProfiler = eventprofiler.Profiler(predicate, 5, 5)
        eventProfiler.run(feed, True)
        self.assertEqual(eventProfiler.getResults().getEventCount(), 0)

    def testOneEvent(self):
        feed = yahoofeed.Feed()
        feed.addBarsFromCSV("orcl", common.get_data_file_path("orcl-2000-yahoofinance.csv"))

        predicate = Predicate([datetime.date(2000, 1, 11)])
        eventProfiler = eventprofiler.Profiler(predicate, 5, 5)
        eventProfiler.run(feed, True)
        self.assertEqual(eventProfiler.getResults().getEventCount(), 1)
        self.assertEqual(eventProfiler.getResults().getValues(0)[0], 1.0)
        self.assertEqual(round(eventProfiler.getResults().getValues(5)[0], 5), round(1.016745541, 5))
