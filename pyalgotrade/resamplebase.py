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


import abc

from pyalgotrade.utils import dt


# Returns the slot's beginning datetime.
# frequency in seconds
def get_slot_datetime(dateTime, frequency):
    ts = int(dt.datetime_to_timestamp(dateTime))
    slot = ts / frequency
    slotTs = slot * frequency
    ret = dt.timestamp_to_datetime(slotTs, False)
    if not dt.datetime_is_naive(dateTime):
        ret = dt.localize(ret, dateTime.tzinfo)
    return ret


class Grouper(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, groupDateTime):
        self.__groupDateTime = groupDateTime

    def getDateTime(self):
        return self.__groupDateTime

    @abc.abstractmethod
    def addValue(self, value):
        """Add a value to the group."""
        raise NotImplementedError()

    @abc.abstractmethod
    def getGrouped(self):
        """Return the grouped value."""
        raise NotImplementedError()
