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

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import xmlrpclib
import pickle
import time
import socket
import random
import multiprocessing

import pyalgotrade.logger
from pyalgotrade import barfeed


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


class Worker(object):
    def __init__(self, address, port, workerName=None):
        url = "http://%s:%s/PyAlgoTradeRPC" % (address, port)
        self.__server = xmlrpclib.ServerProxy(url, allow_none=True)
        self.__logger = pyalgotrade.logger.getLogger(workerName)
        if workerName is None:
            self.__workerName = socket.gethostname()
        else:
            self.__workerName = workerName

    def getLogger(self):
        return self.__logger

    def setLogger(self, logger):
        self.__logger = logger

    def getInstrumentsAndBars(self):
        ret = call_and_retry_on_network_error(self.__server.getInstrumentsAndBars, 10)
        ret = pickle.loads(ret)
        return ret

    def getBarsFrequency(self):
        ret = call_and_retry_on_network_error(self.__server.getBarsFrequency, 10)
        ret = int(ret)
        return ret

    def getNextJob(self):
        ret = call_and_retry_on_network_error(self.__server.getNextJob, 10)
        ret = pickle.loads(ret)
        return ret

    def pushJobResults(self, jobId, result, parameters):
        jobId = pickle.dumps(jobId)
        result = pickle.dumps(result)
        parameters = pickle.dumps(parameters)
        workerName = pickle.dumps(self.__workerName)
        call_and_retry_on_network_error(self.__server.pushJobResults, 10, jobId, result, parameters, workerName)

    def __processJob(self, job, barsFreq, instruments, bars):
        bestResult = 0
        parameters = job.getNextParameters()
        bestParams = parameters
        while parameters is not None:
            # Wrap the bars into a feed.
            feed = barfeed.OptimizerBarFeed(barsFreq, instruments, bars)
            # Run the strategy.
            self.getLogger().info("Running strategy with parameters %s" % (str(parameters)))
            result = self.runStrategy(feed, *parameters)
            self.getLogger().info("Result %s" % result)
            if result > bestResult:
                bestResult = result
                bestParams = parameters
            # Run with the next set of parameters.
            parameters = job.getNextParameters()

        assert(bestParams is not None)
        self.pushJobResults(job.getId(), bestResult, bestParams)

    # Run the strategy and return the result.
    def runStrategy(self, feed, parameters):
        raise Exception("Not implemented")

    def run(self):
        # Get the instruments and bars.
        instruments, bars = self.getInstrumentsAndBars()
        barsFreq = self.getBarsFrequency()

        # Process jobs
        job = self.getNextJob()
        while job is not None:
            self.__processJob(job, barsFreq, instruments, bars)
            job = self.getNextJob()


def worker_process(strategyClass, address, port, workerName):
    class MyWorker(Worker):
        def runStrategy(self, barFeed, *args, **kwargs):
            strat = strategyClass(barFeed, *args, **kwargs)
            strat.run()
            return strat.getResult()

    # Create a worker and run it.
    w = MyWorker(address, port, workerName)
    w.run()


def run(strategyClass, address, port, workerCount=None, workerName=None):
    """Executes one or more worker processes that will run a strategy with the bars and parameters supplied by the server.

    :param strategyClass: The strategy class.
    :param address: The address of the server.
    :type address: string.
    :param port: The port where the server is listening for incoming connections.
    :type port: int.
    :param workerCount: The number of worker processes to run. If None then as many workers as CPUs are used.
    :type workerCount: int.
    :param workerName: A name for the worker. A name that identifies the worker. If None, the hostname is used.
    :type workerName: string.
    """

    assert(workerCount is None or workerCount > 0)
    if workerCount is None:
        workerCount = multiprocessing.cpu_count()

    workers = []
    # Build the worker processes.
    for i in range(workerCount):
        workers.append(multiprocessing.Process(target=worker_process, args=(strategyClass, address, port, workerName)))

    # Start workers
    for process in workers:
        process.start()

    # Wait workers
    for process in workers:
        process.join()
