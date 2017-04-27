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
.. moduleauthor:: Massimo Fierro <massimo.fierro@gmail.com>
"""

from pyalgotrade.optimizer.xmlrpcserver import Server
import pyalgotrade.barfeed
import pyalgotrade.logger
import zlib
import cPickle as pickle
from pyalgotrade import bar

logger = pyalgotrade.logger.getLogger(__name__)


class LowMemXmlRpcServer(Server):

    def __init__(self, paramSource, resultSinc,
                 instsAndDataFilenames, feedPickle,
                 address, port, autoStop=True):

        self.defaultBatchSize = 1

        self._instsAndDataFilenames = instsAndDataFilenames
        self._instsAndData = []
        self._feedPickle = feedPickle
        self._feed = pickle.loads(feedPickle)
        for inst, fName in self._instsAndDataFilenames:
            self._feed.addBarsFromCSV(inst, fName)

        Server.__init__(self, paramSource, resultSinc,
                        self._feed, address, port,
                        autoStop)

        self.register_function(self.getFeedPickle,
                               'getFeedPickle')
        self.register_function(self.getInstrumentsAndData,
                               'getInstrumentsAndData')

    def getFeedPickle(self):
        return (self._feedPickle)

    def getInstrumentsAndData(self):
        return (self._instsAndData)

    def serve(self):
        try:
            # Initialize instruments, bars and parameters.
            logger.info("Loading bars")

            self._data = []
            for (inst, fname) in self._instsAndDataFilenames:
                with open(fname, 'r') as f:
                    self._instsAndData.append((inst, f.read()))

            self._Server__barsFreq = self._Server__barFeed.getFrequency()

            if self._Server__autoStopThread:
                self._Server__autoStopThread.start()

            logger.info("Waiting for workers")
            self.serve_forever()

            if self._Server__autoStopThread:
                self._Server__autoStopThread.join()
        finally:
            self._Server__forcedStop = True
