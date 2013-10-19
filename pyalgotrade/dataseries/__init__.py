# PyAlgoTrade
#
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import observer

DEFAULT_MAX_LEN = 1024


def resize_list(list_, size):
    return list_[-1*size:]


# It is important to inherit object to get __getitem__ to work properly.
# Check http://code.activestate.com/lists/python-list/621258/
class DataSeries(object):
    """Base class for data series.

    .. note::
        This is a base class and should not be used directly.
    """

    def __len__(self):
        """Returns the number of elements in the data series."""
        return self.getLength()

    def __getitem__(self, key):
        """Returns the value at a given position/slice. It raises IndexError if the position is invalid,
        or TypeError if the key type is invalid."""
        if isinstance(key, slice):
            return [self[i] for i in xrange(*key.indices(self.getLength()))]
        elif isinstance(key, int):
            if key < 0:
                key += self.getLength()
            if key >= self.getLength() or key < 0:
                raise IndexError("Index out of range")
            return self.getValueAbsolute(key)
        else:
            raise TypeError("Invalid argument type")

    def getFirstValidPos(self):
        raise NotImplementedError()

    def getLength(self):
        raise NotImplementedError()

    # This is similar to __getitem__ for ints, but it shouldn't raise for invalid positions.
    def getValueAbsolute(self, pos):
        raise NotImplementedError()

    def getDateTimes(self):
        """Returns a list of :class:`datetime.datetime` associated with each value."""
        raise NotImplementedError()


class SequenceDataSeries(DataSeries):
    """A DataSeries that holds values in a sequence in memory.

    :param maxLen: The maximum number of values to hold. If not None, it must be greater than 0.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    """

    def __init__(self, maxLen=DEFAULT_MAX_LEN):
        assert(maxLen is None or maxLen > 0)
        self.__newValueEvent = observer.Event()
        # I'm not using collections.deque because:
        # 1: Random access is slower.
        # 2: Slicing is not supported.
        self.__values = []
        self.__dateTimes = []
        self.__maxLen = maxLen

    def __len__(self):
        return len(self.__values)

    def __getitem__(self, key):
        return self.__values[key]

    def setMaxLen(self, maxLen):
        """Sets the maximum number of values to hold and resizes accordingly if necessary."""
        self.__maxLen = maxLen
        if maxLen is not None and len(self.__values) > maxLen:
            self.__values = resize_list(self.__values, maxLen)
            self.__dateTimes = resize_list(self.__dateTimes, maxLen)

    def getMaxLen(self):
        """Returns the maximum number of values to hold."""
        return self.__maxLen

    # Event handler receives:
    # 1: Dataseries generating the event
    # 2: The datetime for the new value
    # 3: The new value
    def getNewValueEvent(self):
        return self.__newValueEvent

    def getFirstValidPos(self):
        return 0

    def getLength(self):
        return len(self.__values)

    def getValueAbsolute(self, pos):
        ret = None
        if pos >= 0 and pos < len(self.__values):
            ret = self.__values[pos]
        return ret

    def append(self, value):
        """Appends a value."""
        self.appendWithDateTime(None, value)

    def appendWithDateTime(self, dateTime, value):
        """
        Appends a value with an associated datetime.

        .. note::
            If dateTime is not None, it must be greater than the last one.
        """
        if dateTime is not None and len(self.__dateTimes) != 0 and self.__dateTimes[-1] >= dateTime:
            raise Exception("Invalid datetime. It must be bigger than that last one")
        self.__dateTimes.append(dateTime)
        self.__values.append(value)
        assert(len(self.__values) == len(self.__dateTimes))

        # Check bounds
        if self.__maxLen is not None and len(self.__values) > self.__maxLen:
            self.__dateTimes.pop(0)
            self.__values.pop(0)

        self.getNewValueEvent().emit(self, dateTime, value)

    def getDateTimes(self):
        return self.__dateTimes
