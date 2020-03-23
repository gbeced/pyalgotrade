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

import six

from pyalgotrade import barfeed
from pyalgotrade import bar
from pyalgotrade import utils


# A non real-time BarFeed responsible for:
# - Holding bars in memory.
# - Aligning them with respect to time.
#
# Subclasses should:
# - Forward the call to start() if they override it.

class BarFeed(barfeed.BaseBarFeed):
    def __init__(self, frequency, maxLen=None):
        super(BarFeed, self).__init__(frequency, maxLen)

        self.__bars = {}
        self.__nextPos = {}
        self.__started = False
        self.__currDateTime = None

    ## BEGIN observer.Subject abstractmethods
    def start(self):
        super(BarFeed, self).start()
        self.__started = True

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        ret = True
        # Check if there is at least one more bar to return.
        for pair, bars in six.iteritems(self.__bars):
            nextPos = self.__nextPos[pair]
            if nextPos < len(bars):
                ret = False
                break
        return ret

    def peekDateTime(self):
        ret = None

        for pair, bars in six.iteritems(self.__bars):
            nextPos = self.__nextPos[pair]
            if nextPos < len(bars):
                ret = utils.safe_min(ret, bars[nextPos].getDateTime())
        return ret
    ## END observer.Subject abstractmethods

    ## BEGIN barfeed.BaseBarFeed abstractmethods
    def getCurrentDateTime(self):
        return self.__currDateTime

    def getNextBars(self):
        # All bars must have the same datetime. We will return all the ones with the smallest datetime.
        smallestDateTime = self.peekDateTime()

        if smallestDateTime is None:
            return None

        # Make a second pass to get all the bars that have the smallest datetime.
        ret = []
        for pair, bars in six.iteritems(self.__bars):
            nextPos = self.__nextPos[pair]
            if nextPos < len(bars) and bars[nextPos].getDateTime() == smallestDateTime:
                # Check if there are duplicate bars (with the same datetime).
                if self.__currDateTime == smallestDateTime:
                    raise Exception("Duplicate bars found for %s on %s" % (pair, smallestDateTime))
                assert bars[nextPos].pairToKey() == pair, "bar/pair mismatch"
                ret.append(bars[nextPos])
                self.__nextPos[pair] += 1

        self.__currDateTime = smallestDateTime
        return bar.Bars(ret)
    ## END barfeed.BaseBarFeed abstractmethods

    def reset(self):
        self.__nextPos = {}
        for pair in self.__bars.keys():
            self.__nextPos.setdefault(pair, 0)
        self.__currDateTime = None
        super(BarFeed, self).reset()

    def addBarsFromSequence(self, instrument, priceCurrency, bars):
        if self.__started:
            raise Exception("Can't add more bars once you started consuming bars")

        key = bar.pair_to_key(instrument, priceCurrency)
        self.__bars.setdefault(key, [])
        self.__nextPos.setdefault(key, 0)

        # Add and sort the bars
        self.__bars[key].extend(bars)
        self.__bars[key].sort(key=lambda b: b.getDateTime())

        self.registerDataSeries(key)

    def loadAll(self):
        for dateTime, bars in self:
            pass
