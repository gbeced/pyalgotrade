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


def lt(v1, v2):
    if v1 is None:
        return True
    elif v2 is None:
        return False
    else:
        return v1 < v2


# Returns (values, ix1, ix2)
# values1 and values2 are assumed to be sorted
def intersect(values1, values2, skipNone=False):
    ix1 = []
    ix2 = []
    values = []

    i1 = 0
    i2 = 0
    while i1 < len(values1) and i2 < len(values2):
        v1 = values1[i1]
        v2 = values2[i2]
        if v1 == v2 and (v1 is not None or skipNone is False):
            ix1.append(i1)
            ix2.append(i2)
            values.append(v1)
            i1 += 1
            i2 += 1
        elif lt(v1, v2):
            i1 += 1
        else:
            i2 += 1

    return (values, ix1, ix2)


# Like a collections.deque but using a numpy.array.
class NumPyDeque(object):
    def __init__(self, maxLen, dtype=float):
        assert maxLen > 0, "Invalid maximum length"

        self.__values = np.empty(maxLen, dtype=dtype)
        self.__maxLen = maxLen
        self.__nextPos = 0

    def getMaxLen(self):
        return self.__maxLen

    def append(self, value):
        if self.__nextPos < self.__maxLen:
            self.__values[self.__nextPos] = value
            self.__nextPos += 1
        else:
            # Shift items to the left and put the last value.
            # I'm not using np.roll to avoid creating a new array.
            self.__values[0:-1] = self.__values[1:]
            self.__values[self.__nextPos - 1] = value

    def data(self):
        # If all values are not initialized, return a portion of the array.
        if self.__nextPos < self.__maxLen:
            ret = self.__values[0:self.__nextPos]
        else:
            ret = self.__values
        return ret

    def resize(self, maxLen):
        assert maxLen > 0, "Invalid maximum length"

        # Create empty, copy last values and swap.
        values = np.empty(maxLen, dtype=self.__values.dtype)
        lastValues = self.__values[0:self.__nextPos]
        values[0:min(maxLen, len(lastValues))] = lastValues[-1*min(maxLen, len(lastValues)):]
        self.__values = values

        self.__maxLen = maxLen
        if self.__nextPos >= self.__maxLen:
            self.__nextPos = self.__maxLen

    def __len__(self):
        return self.__nextPos

    def __getitem__(self, key):
        return self.data()[key]


# I'm not using collections.deque because:
# 1: Random access is slower.
# 2: Slicing is not supported.
class ListDeque(object):
    def __init__(self, maxLen):
        assert maxLen > 0, "Invalid maximum length"

        self.__values = []
        self.__maxLen = maxLen

    def getMaxLen(self):
        return self.__maxLen

    def append(self, value):
        self.__values.append(value)
        # Check bounds
        if len(self.__values) > self.__maxLen:
            self.__values.pop(0)

    def data(self):
        return self.__values

    def resize(self, maxLen):
        assert maxLen > 0, "Invalid maximum length"

        self.__maxLen = maxLen
        self.__values = self.__values[-1*maxLen:]

    def __len__(self):
        return len(self.__values)

    def __getitem__(self, key):
        return self.__values[key]
