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


class ParametersIterator:
    def __init__(self, paramCount):
        self.__paramRanges = [None for i in range(paramCount)]
        self.__currentValues = [None for i in range(paramCount)]

    def setRange(self, paramIndex, begin, end):
        self.__paramRanges[paramIndex] = (begin, end)
        if self.__currentValues[paramIndex] is None:
            self.__currentValues[paramIndex] = begin

    def setCurrentValue(self, paramIndex, value):
        self.__currentValues[paramIndex] = value

    def getCurrent(self):
        ret = None
        if self.__currentValues is not None:
            ret = tuple(self.__currentValues)
        return ret

    def __incrementCurrent(self, paramIndex):
        nextValue = self.__currentValues[paramIndex] + 1
        if nextValue >= self.__paramRanges[paramIndex][1]:
            self.__currentValues[paramIndex] = self.__paramRanges[paramIndex][0]
            if paramIndex != 0:
                self.__incrementCurrent(paramIndex - 1)
            else:
                self.__currentValues = None
        else:
            self.__currentValues[paramIndex] = nextValue

    def moveNext(self):
        if self.__currentValues is not None:
            self.__incrementCurrent(len(self.__paramRanges) - 1)

    def __iter__(self):
        return self

    def next(self):
        ret = self.getCurrent()
        if ret is not None:
            self.moveNext()
        else:
            raise StopIteration()
        return ret
