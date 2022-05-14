# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import socket
import multiprocessing
import retrying

from six.moves import xmlrpc_client

import pyalgotrade.logger
from pyalgotrade import barfeed
from pyalgotrade.optimizer import serialization

wait_exponential_multiplier = 500
wait_exponential_max = 10000
stop_max_delay = 10000


def any_exception(exception):
    return True


@retrying.retry(wait_exponential_multiplier=wait_exponential_multiplier, wait_exponential_max=wait_exponential_max, stop_max_delay=stop_max_delay, retry_on_exception=any_exception)
def retry_on_network_error(function, *args, **kwargs):
    return function(*args, **kwargs)


class Worker(object):
    def __init__(self, address, port, workerName=None):
        url = f"http://{address}:{port}/PyAlgoTradeRPC"
        self.__logger = pyalgotrade.logger.getLogger(workerName)
        self.__server = xmlrpc_client.ServerProxy(url, allow_none=True)
        self.__workerName = socket.gethostname() if workerName is None else workerName

    def getLogger(self):
        return self.__logger

    def getInstrumentsAndBars(self):
        ret = retry_on_network_error(self.__server.getInstrumentsAndBars)
        ret = serialization.loads(ret)
        return ret

    def getBarsFrequency(self):
        ret = retry_on_network_error(self.__server.getBarsFrequency)
        ret = int(ret)
        return ret

    def getNextJob(self):
        ret = retry_on_network_error(self.__server.getNextJob)
        ret = serialization.loads(ret)
        return ret

    def pushJobResults(self, jobId, result, parameters):
        jobId = serialization.dumps(jobId)
        result = serialization.dumps(result)
        parameters = serialization.dumps(parameters)
        workerName = serialization.dumps(self.__workerName)
        retry_on_network_error(self.__server.pushJobResults, jobId, result, parameters, workerName)

    def __processJob(self, job, barsFreq, instruments, bars):
        bestResult = None
        parameters = job.getNextParameters()
        bestParams = parameters
        while parameters is not None:
            # Wrap the bars into a feed.
            feed = barfeed.OptimizerBarFeed(barsFreq, instruments, bars)
            # Run the strategy.
            self.getLogger().info(f"Running strategy with parameters {str(parameters)}")
            result = None
            try:
                result = self.runStrategy(feed, *parameters)
            except Exception as e:
                self.getLogger().exception(
                    f"Error running strategy with parameters {str(parameters)}: {e}"
                )

            self.getLogger().info(f"Result {result}")
            if bestResult is None or result > bestResult:
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
        except Exception as e:
            self.getLogger().exception(f"Finished running with errors: {e}")


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

    workers = [
        multiprocessing.Process(
            target=worker_process,
            args=(strategyClass, address, port, workerName),
        )
        for _ in range(workerCount)
    ]

    # Start workers
    for process in workers:
        process.start()

    # Wait workers
    for process in workers:
        process.join()
