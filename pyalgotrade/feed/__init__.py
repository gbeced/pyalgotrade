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


def feed_iterator(feed):
    feed.start()
    try:
        while not feed.eof():
            yield feed._getNextValuesAndUpdateDS()
    finally:
        feed.stop()
        feed.join()


class BaseFeed(observer.Subject):
    """
    Base class for feeds.

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

        self.__ds = {}
        self.__event = observer.Event()
        self.__maxLen = maxLen

    def __iter__(self):
        return feed_iterator(self)

    def __getitem__(self, key):
        """Returns the :class:`pyalgotrade.dataseries.DataSeries` for a given key."""
        return self.__ds[key]

    def __contains__(self, key):
        """Returns True if a :class:`pyalgotrade.dataseries.DataSeries` for the given key is available."""
        return key in self.__ds

    # Subclasses should implement this and return the appropriate dataseries for the given key.
    @abc.abstractmethod
    def createDataSeries(self, key, maxLen):
        raise NotImplementedError()

    # Subclasses should implement this and return a tuple with two elements:
    # 1: datetime.datetime.
    # 2: dictionary or dict-like object.
    @abc.abstractmethod
    def _getNextValues(self):
        raise NotImplementedError()

    # BEGIN observer.Subject abstractmethods
    def dispatch(self):
        dateTime, values = self._getNextValuesAndUpdateDS()
        if dateTime is not None:
            self.__event.emit(dateTime, values)
        return dateTime is not None
    # END observer.Subject abstractmethods

    def reset(self):
        keys = list(self.__ds.keys())
        self.__ds = {}
        for key in keys:
            self.registerDataSeries(key)

    def registerDataSeries(self, key):
        if key not in self.__ds:
            self.__ds[key] = self.createDataSeries(key, self.__maxLen)

    def _getNextValuesAndUpdateDS(self):
        dateTime, values = self._getNextValues()
        if dateTime is not None:
            for key, value in values.items():
                # Get or create the datseries for each key.
                try:
                    ds = self.__ds[key]
                except KeyError:
                    ds = self.createDataSeries(key, self.__maxLen)
                    self.__ds[key] = ds
                ds.appendWithDateTime(dateTime, value)
        return (dateTime, values)

    def getNewValuesEvent(self):
        """Returns the event that will be emitted when new values are available.
        To subscribe you need to pass in a callable object that receives two parameters:

         1. A :class:`datetime.datetime` instance.
         2. The new value.
        """
        return self.__event

    def getKeys(self):
        return list(self.__ds.keys())

    def getDataSeries(self, key):
        """
        Returns the :class:`pyalgotrade.dataseries.DataSeries` for a given key, or None if it is not found.
        """
        return self.__ds.get(key)

    def getAllDataSeries(self):
        """
        Returns all :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return list(self.__ds.values())
