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

from pyalgotrade import dataseries


def datetime_aligned(ds1, ds2, maxLen=None):
    """
    Returns two dataseries that exhibit only those values whose datetimes are in both dataseries.

    :param ds1: A DataSeries instance.
    :type ds1: :class:`DataSeries`.
    :param ds2: A DataSeries instance.
    :type ds2: :class:`DataSeries`.
    :param maxLen: The maximum number of values to hold for the returned :class:`DataSeries`.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    aligned1 = dataseries.SequenceDataSeries(maxLen)
    aligned2 = dataseries.SequenceDataSeries(maxLen)
    Syncer(ds1, ds2, aligned1, aligned2)
    return (aligned1, aligned2)


# This class is responsible for filling 2 dataseries when 2 other dataseries get new values.
class Syncer(object):
    def __init__(self, sourceDS1, sourceDS2, destDS1, destDS2):
        self.__values1 = []  # (datetime, value)
        self.__values2 = []  # (datetime, value)
        self.__destDS1 = destDS1
        self.__destDS2 = destDS2
        sourceDS1.getNewValueEvent().subscribe(self.__onNewValue1)
        sourceDS2.getNewValueEvent().subscribe(self.__onNewValue2)
        # Source dataseries will keep a reference to self and that will prevent from getting this destroyed.

    # Scan backwards for the position of dateTime in ds.
    def __findPosForDateTime(self, values, dateTime):
        ret = None
        i = len(values) - 1
        while i >= 0:
            if values[i][0] == dateTime:
                ret = i
                break
            elif values[i][0] < dateTime:
                break
            i -= 1
        return ret

    def __onNewValue1(self, dataSeries, dateTime, value):
        pos2 = self.__findPosForDateTime(self.__values2, dateTime)
        # If a value for dateTime was added to first dataseries, and a value for that same datetime is also in the second one
        # then append to both destination dataseries.
        if pos2 is not None:
            self.__append(dateTime, value, self.__values2[pos2][1])
            # Reset buffers.
            self.__values1 = []
            self.__values2 = self.__values2[pos2+1:]
        else:
            # Since source dataseries may not hold all the values we need, we need to buffer manually.
            self.__values1.append((dateTime, value))

    def __onNewValue2(self, dataSeries, dateTime, value):
        pos1 = self.__findPosForDateTime(self.__values1, dateTime)
        # If a value for dateTime was added to second dataseries, and a value for that same datetime is also in the first one
        # then append to both destination dataseries.
        if pos1 is not None:
            self.__append(dateTime, self.__values1[pos1][1], value)
            # Reset buffers.
            self.__values1 = self.__values1[pos1+1:]
            self.__values2 = []
        else:
            # Since source dataseries may not hold all the values we need, we need to buffer manually.
            self.__values2.append((dateTime, value))

    def __append(self, dateTime, value1, value2):
        self.__destDS1.appendWithDateTime(dateTime, value1)
        self.__destDS2.appendWithDateTime(dateTime, value2)
