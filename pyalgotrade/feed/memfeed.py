# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import feed
from pyalgotrade import dataseries


class MemFeed(feed.BaseFeed):
    def __init__(self, maxLen=dataseries.DEFAULT_MAX_LEN):
        feed.BaseFeed.__init__(self, maxLen)
        self.__values = []
        self.__nextIdx = 0

    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        if self.__nextIdx < len(self.__values):
            return False
        else:
            return True

    def peekDateTime(self):
        ret = None
        if self.__nextIdx < len(self.__values):
            ret = self.__values[self.__nextIdx][0]
        return ret

    def isRealTime(self):
        return False

    def createDataSeries(self, key, maxLen):
        return dataseries.SequenceDataSeries(maxLen)

    def getNextValues(self):
        ret = (None, None)
        if self.__nextIdx < len(self.__values):
            ret = self.__values[self.__nextIdx]
            self.__nextIdx += 1
        return ret

    # Add values to the feed. values should be a sequence of tupes. The tupes should have two elements:
    # 1: datetime.datetime.
    # 2: dictionary or dict-like object.
    def addValues(self, values):
        if len(values):
            # Register a dataseries for each item.
            for key in values[0][1].keys():
                self.registerDataSeries(key)

            self.__values.extend(values)
            cmpFun = lambda x, y: cmp(x[0], y[0])
            self.__values.sort(cmpFun)
