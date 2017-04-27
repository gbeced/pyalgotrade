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

from pyalgotrade.optimizer import worker
import multiprocessing
import socket
import zlib
import uuid
import os
import time
import random
import gc
try:
    import cPickle as pickle
except:
    import pickle


def call_function(function, *args, **kwargs):
    return function(*args, **kwargs)


def call_and_retry_on_network_error(function, retryCount, *args, **kwargs):
    ret = None
    while retryCount > 0:
        retryCount -= 1
        try:
            ret = call_function(function, *args, **kwargs)
            return ret
        except socket.error:
            time.sleep(random.randint(1, 3))
    ret = call_function(function, *args, **kwargs)
    return ret


def worker_process(strategyClass, address, port, workerName):
    class MyWorker(GmassXmlRcpClient):
        def runStrategy(self, barFeed, *args, **kwargs):
            strat = strategyClass(barFeed, *args, **kwargs)
            strat.run()
            return strat.getResult()

    # Create a worker and run it.
    w = MyWorker(address, port, workerName)
    w.run()


def run(strategyClass, address, port, workerCount=None, workerName=None):
    """Executes one or more worker processes that will run a strategy with the
        bars and parameters supplied by the server.

    :param strategyClass: The strategy class.
    :param address: The address of the server.
    :type address: string.
    :param port: The port where the server is listening for incoming
        connections.
    :type port: int.
    :param workerCount: The number of worker processes to run. If None then as
        many workers as CPUs are used.
    :type workerCount: int.
    :param workerName: A name for the worker. A name that identifies the
        worker. If None, the hostname is used.
    :type workerName: string.
    """

    assert(workerCount is None or workerCount > 0)
    if workerCount is None:
        workerCount = multiprocessing.cpu_count()

    workers = []
    # Build the worker processes.
    for i in range(workerCount):
        workers.append(multiprocessing.Process(
            target=worker_process, args=(
                strategyClass, address, port, workerName)))

    # Start workers
    for process in workers:
        process.start()

    # Wait workers
    for process in workers:
        process.join()


class LowMemXmlRcpWorker(worker.Worker):
    def __init__(self, address, port, workerName=None):
        super(LowMemXmlRcpWorker, self).__init__(address, port, workerName)

    def getFeedPickle(self):
        ret = call_and_retry_on_network_error(
            self._Worker__server.getFeedPickle, 10)
        return ret

    def getInstrumentsAndData(self):
        instsAndData = call_and_retry_on_network_error(
            self._Worker__server.getInstrumentsAndData, 10)
        # for (inst, data) in instsAndData:
        #     print("Received instrument {} + data".format(inst))
        return instsAndData

    def _processJob(self, job):
        bestResult = None
        parameters = job.getNextParameters()
        bestParams = parameters
        while parameters is not None:
            feed = self._resetFeed()
            # Run the strategy.
            self.getLogger().info(
                "Running strategy with parameters %s" % (str(parameters)))
            result = None
            try:
                result = self.runStrategy(feed, *parameters)
            except Exception, e:
                self.getLogger().exception(
                    "Error running strategy with parameters %s: %s" % (
                        str(parameters), e))
            self.getLogger().info("Result %s" % result)
            if bestResult is None or result > bestResult:
                bestResult = result
                bestParams = parameters
            # Run with the next set of parameters.
            parameters = job.getNextParameters()

        assert(bestParams is not None)
        self.pushJobResults(job.getId(), bestResult, bestParams)

    def _resetFeed(self):
        feed = None
        feedPickle = self.getFeedPickle()
        feed = pickle.loads(feedPickle)
        for (inst, fname) in self._instsAndDataFilenames:
            feed.addBarsFromCSV(inst, fname)
        return feed

    def run(self):
        try:
            self.getLogger().info("Started running")
            # Get the instruments and bars.
            barsFreq = self.getBarsFrequency()

            self._instsAndData = self.getInstrumentsAndData()
            self._instsAndDataFilenames = []

            for (inst, data) in self._instsAndData:
                fname = str(uuid.uuid1())
                self._instsAndDataFilenames.append((inst, fname))
                with open(fname, 'w') as f:
                    f.write(data)

            # Process jobs
            job = self.getNextJob()
            while job is not None:
                self._resetFeed()
                self._processJob(job)
                job = self.getNextJob()
            self.getLogger().info("Finished running")
        except Exception, e:
            self.getLogger().exception(
                "Finished running with errors: %s" % (e))
        finally:
            if hasattr(self, "_instsAndDataFilenames") and (
                    self._instsAndDataFilenames is not None):
                for (inst, fName) in self._instsAndDataFilenames:
                    os.remove(fName)
