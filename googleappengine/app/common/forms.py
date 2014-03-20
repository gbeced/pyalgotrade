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

import cgi


class Form:
    def __init__(self, request, fieldNames):
        self.__values = {}
        for name in fieldNames:
            self.__values[name] = request.get(name)

    def setRawValue(self, name, value):
        self.__values[name] = value

    def getRawValue(self, name):
        return self.__values[name]

    def getSafeValue(self, name):
        ret = self.getRawValue(name)
        if ret is not None:
            ret = cgi.escape(ret)
        return ret

    def getValuesForTemplate(self):
        ret = {}
        for name in self.__values.keys():
            ret[name] = self.getSafeValue(name)
        return ret
