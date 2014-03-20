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

import time


class Timer:
    def __init__(self):
        self.__started = time.time()

    def secondsElapsed(self):
        """Returns an int with the number of seconds ellapsed since the instance was created."""
        return int(time.time() - self.__started)

    def minutesElapsed(self):
        """Returns an float with the number of seconds ellapsed since the instance was created."""
        return self.secondsElapsed() / float(60)
