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

import abc

from pyalgotrade import observer
from pyalgotrade import dataseries
from pyalgotrade import bar

def feed_iterator(feed):
    feed.start()
    try:
        while not feed.eof():
            yield feed.getNextValuesAndUpdateDS()
    finally:
        feed.stop()
        feed.join()


class BaseFeed(observer.Subject):
    """Base class for feeds.

    :param maxLen: The maximum number of values that each :class:`pyalgotrade.dataseries.DataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded
        from the opposite end.
    :type maxLen: int.

    .. note::
        This is a base class and should not be used directly.
    """

    def __init__(self, maxLen):
        super(BaseFeed, self).__init__()

        maxLen = dataseries.get_checked_max_len(maxLen)
        self.__registered_ds = []
        self.__ds = {}
        self.__event = observer.Event()
        self.__maxLen = maxLen

    def reset(self):
        self.__ds = {}
        for key, freq in self.__registered_ds:
            self.registerDataSeries(key, freq)

    # Subclasses should implement this and return the appropriate dataseries for the given key.
    @abc.abstractmethod
    def createDataSeries(self, key, maxLen):
        raise NotImplementedError()

    # Subclasses should implement this and return a tuple with two elements:
    # 1: datetime.datetime.
    # 2: dictionary or dict-like object.
    @abc.abstractmethod
    def getNextValues(self):
        raise NotImplementedError()

    def registerDataSeries(self, key, freq = bar.Frequency.UNKNOWN):
        if key not in self.__ds:
            self.__ds[key] = {}
        for i in self.__registered_ds:
            k, v = i
            if k == key and v == freq:
                return
        self.__ds[key][freq] = self.createDataSeries(key, self.__maxLen)
        self.__registered_ds.append((key, freq))

    def getNextValuesAndUpdateDS(self):
        dateTime, values, freq = self.getNextValues()
        if dateTime is not None:
            for key, value in values.items():
                # Get or create the datseries for each key.
                try:
                    ds = self.__ds[key][freq]
                except KeyError:
                    ds = self.createDataSeries(key, self.__maxLen)
                    if key not in self.__ds.keys():
                        self.__ds[key] = {}
                    self.__ds[key][freq] = ds
                ds.appendWithDateTime(dateTime, value)
        return (dateTime, values, freq)

    def __iter__(self):
        return feed_iterator(self)

    def getNewValuesEvent(self):
        """Returns a event that will be emitted when new values are available.
        To subscribe you need to pass in a callable object that receives two parameters:

         1. A :class:`datetime.datetime` instance.
         2. The new value.
        """
        return self.__event

    def dispatch(self):
        dateTime, values, _ = self.getNextValuesAndUpdateDS()
        if dateTime is not None:
            self.__event.emit(dateTime, values)
        return dateTime is not None

    def getKeys(self):
        return list(self.__ds.keys())

    def __getitem__(self, val):
        """Returns the :class:`pyalgotrade.dataseries.DataSeries` for a given key."""
        if isinstance(val, tuple):
            key, freq = val
            return self.__ds[key][freq]
        else:
            assert len(self.__ds[val]) == 1
            return list(self.__ds[val].values())[0]

    def __contains__(self, val):
        """Returns True if a :class:`pyalgotrade.dataseries.DataSeries` for the given key is available."""
        if isinstance(val, tuple):
            key, freq = val
        else:
            key, freq = val, None
        if freq is None:
            return key in self.__ds
        else:
            return (key in self.__ds and freq in self.__ds[key])