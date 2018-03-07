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

import logging
import multiprocessing
import os
import random
import socket
import threading

from pyalgotrade.optimizer import base
from pyalgotrade.optimizer import server
from pyalgotrade.optimizer import worker
from pyalgotrade.optimizer import xmlrpcserver

logger = logging.getLogger(__name__)


class ServerThread(threading.Thread):
    def __init__(self, server):
        super(ServerThread, self).__init__()
        self.__server = server

    def run(self):
        self.__results = self.__server.serve()


def worker_process(strategyClass, port, logLevel):
    class Worker(worker.Worker):
        def runStrategy(self, barFeed, *args, **kwargs):
            strat = strategyClass(barFeed, *args, **kwargs)
            strat.run()
            return strat.getResult()

    # Create a worker and run it.
    try:
        name = "worker-%s" % (os.getpid())
        w = Worker("localhost", port, name)
        w.getLogger().setLevel(logLevel)
        w.run()
    except Exception as e:
        w.getLogger().exception("Failed to run worker: %s" % (e))


def find_port():
    while True:
        ret = random.randint(1025, 65536)
        try:
            s = socket.socket()
            s.bind(("localhost", ret))
            s.close()
            return ret
        except socket.error:
            pass


def wait_process(p):
    timeout = 10
    p.join(timeout)
    while p.is_alive():
        p.join(timeout)


def run(strategyClass, barFeed, strategyParameters, workerCount=None, logLevel=logging.ERROR):
    """Executes many instances of a strategy in parallel and finds the parameters that yield the best results.

    :param strategyClass: The strategy class.
    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is
        a tuple that holds parameter values**.
    :param workerCount: The number of strategies to run in parallel. If None then as many workers as CPUs are used.
    :type workerCount: int.
    :param logLevel: The log level. Defaults to **logging.ERROR**.
    :rtype: A :class:`Results` instance with the best results found.
    """

    assert(workerCount is None or workerCount > 0)
    if workerCount is None:
        workerCount = multiprocessing.cpu_count()

    ret = None
    workers = []
    port = find_port()
    if port is None:
        raise Exception("Failed to find a port to listen")

    # Build and start the server thread before the worker processes.
    # We'll manually stop the server once workers have finished.
    paramSource = base.ParameterSource(strategyParameters)
    resultSinc = base.ResultSinc()
    srv = xmlrpcserver.Server(paramSource, resultSinc, barFeed, "localhost", port, False)
    serverThread = ServerThread(srv)
    serverThread.start()

    try:
        # Build the worker processes.
        for i in range(workerCount):
            workers.append(multiprocessing.Process(
                target=worker_process,
                args=(strategyClass, port, logLevel))
            )

        logger.info("Executing workers")

        # Start workers
        for process in workers:
            process.start()

        # Wait workers
        for process in workers:
            wait_process(process)

        logger.info("All workers finished")
    finally:
        # Stop and wait the server to finish.
        srv.stop()
        serverThread.join()

        bestResult, bestParameters = resultSinc.getBest()
        if bestResult is not None:
            ret = server.Results(bestParameters.args, bestResult)

    return ret
