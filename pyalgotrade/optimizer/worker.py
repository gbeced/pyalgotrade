# PyAlgoTrade
#
# Copyright 2011-2017 Gabriel Martin Becedillas Ruiz
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
import socket
import multiprocessing
import retrying

import pyalgotrade.logger
from pyalgotrade import barfeed
from pyalgotrade.optimizer import base

wait_exponential_multiplier = 500
wait_exponential_max = 10000
stop_max_delay = 10000


def any_exception(exception):
    return True


@retrying.retry(wait_exponential_multiplier=wait_exponential_multiplier, wait_exponential_max=wait_exponential_max, stop_max_delay=stop_max_delay, retry_on_exception=any_exception)
def retry_on_network_error(function, *args, **kwargs):
    return function(*args, **kwargs)


class Worker(object):
    def __init__(self, address, port, strategyRunner, resultSincFactory, workerName=None):
        url = "http://%s:%s/PyAlgoTradeRPC" % (address, port)
        self.__logger = pyalgotrade.logger.getLogger(workerName)
        self.__server = xmlrpclib.ServerProxy(url, allow_none=True)
        if workerName is None:
            self.__workerName = socket.gethostname()
        else:
            self.__workerName = workerName
        self.__strategyRunner = strategyRunner
        self.__resultSincFactory = resultSincFactory

    def getLogger(self):
        return self.__logger

    def getInstrumentsAndBars(self):
        ret = retry_on_network_error(self.__server.getInstrumentsAndBars)
        ret = pickle.loads(ret)
        return ret

    def getBarsFrequency(self):
        ret = retry_on_network_error(self.__server.getBarsFrequency)
        ret = int(ret)
        return ret

    def getNextJob(self):
        ret = retry_on_network_error(self.__server.getNextJob)
        ret = pickle.loads(ret)
        return ret

    def pushJobResults(self, jobId, resultSinc):
        jobId = pickle.dumps(jobId)
        resultSinc = pickle.dumps(resultSinc)
        workerName = pickle.dumps(self.__workerName)
        retry_on_network_error(self.__server.pushJobResults, jobId, resultSinc, workerName)

    def __processJob(self, job, barsFreq, instruments, bars):
        parameters = job.getNextParameters()
        resultSinc = self.__resultSincFactory.create()
        while parameters is not None:
            # Wrap the bars into a feed.
            feed = barfeed.OptimizerBarFeed(barsFreq, instruments, bars)
            # Run the strategy.
            self.getLogger().info("Running strategy with parameters %s" % (str(parameters)))
            result = None
            try:
                result = self.__strategyRunner.runStrategy(feed, parameters)
            except Exception, e:
                self.getLogger().exception("Error running strategy with parameters %s: %s" % (str(parameters), e))
            self.getLogger().info("Result %s" % result)
            resultSinc.push(result, parameters)
            # Run with the next set of parameters.
            parameters = job.getNextParameters()

        self.pushJobResults(job.getId(), resultSinc)

    def run(self):
        try:
            self.getLogger().info("Started running")
            # Get the instruments and bars.
            instruments, bars = self.getInstrumentsAndBars()
            barsFreq = self.getBarsFrequency()

            # Process jobs
            job = self.getNextJob()
            while job is not None:
                self.__processJob(job, barsFreq, instruments, bars)
                job = self.getNextJob()
            self.getLogger().info("Finished running")
        except Exception, e:
            self.getLogger().exception("Finished running with errors: %s" % (e))


def worker_process(address, port, workerName, strategyRunner, resultSincFactory):
    # Create a worker and run it.
    w = Worker(address, port, strategyRunner, resultSincFactory, workerName=workerName)
    w.run()


def startWorker(address, port, strategyRunner, resultSincFactory, workerCount=None, workerName=None):
    """Executes one or more worker processes that will run a strategy with the bars and parameters supplied by the server.

    :param address: The address of the server.
    :type address: string.
    :param port: The port where the server is listening for incoming connections.
    :type port: int.
    :param strategyRunner: The strategy executor defining how worker should handle the bars and parameters.
    :type strategyRunner: class:`pyalgotrade.optimizer.base.StrategyRunner`.
    :param resultSincFactory: The factory to create the ResultSinc object which is used to summarize strategy results.
    :type resultSincFactory: :class:`pyalgotrade.optimizer.base.ResultSincFactory`.
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
        workers.append(multiprocessing.Process(target=worker_process, args=(address, port, workerName, strategyRunner, resultSincFactory)))

    # Start workers
    for process in workers:
        process.start()

    # Wait workers
    for process in workers:
        process.join()


def run(strategyClass, address, port, workerCount=None, workerName=None):
    """Start workers to find the best strategy result with the given strategy

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
    strategyRunner = base.AnyStrategyRunner(strategyClass)

    resultSincFactory = base.BestResultFactory()

    startWorker(address, port, strategyRunner, resultSincFactory, workerCount=workerCount, workerName=workerName)
