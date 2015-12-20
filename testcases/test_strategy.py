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

import datetime

from pyalgotrade import strategy


class BaseTestStrategy(strategy.BaseStrategy):
    def __init__(self, barFeed, broker, maxMinutes=5):
        super(BaseTestStrategy, self).__init__(barFeed, broker)
        self.posExecutionInfo = []
        self.ordersUpdated = []
        self.orderExecutionInfo = []
        self.begin = datetime.datetime.now()
        self.deadline = self.begin + datetime.timedelta(minutes=maxMinutes)

    def onOrderUpdated(self, order):
        self.ordersUpdated.append(order)
        self.orderExecutionInfo.append(order.getExecutionInfo())

    def onEnterOk(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onEnterCanceled(self, position):
        self.posExecutionInfo.append(position.getEntryOrder().getExecutionInfo())

    def onExitOk(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())

    def onExitCanceled(self, position):
        self.posExecutionInfo.append(position.getExitOrder().getExecutionInfo())

    def onIdle(self):
        if datetime.datetime.now() >= self.deadline:
            self.stop()
