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

import inspect


class Class:
    def __init__(self, fullClassName):
        parts = fullClassName.split(".")

        if len(parts) > 1:
            mod = __import__(".".join(parts[0:-1]))
            for item in parts[1:-1]:
                mod = getattr(mod, item)
            self.__cls = getattr(mod, parts[-1])
        else:
            self.__cls = locals()[fullClassName]

    def getMethodParams(self, methodName):
        # Return args
        return inspect.getargspec(getattr(self.__cls, methodName))[0]

    def getClass(self):
        return self.__cls
