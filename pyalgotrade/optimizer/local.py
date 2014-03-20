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

import multiprocessing
import threading
import logging
import socket
import random
import os

from pyalgotrade.optimizer import server
from pyalgotrade.optimizer import worker


def server_thread(srv, barFeed, strategyParameters, port):
    srv.serve(barFeed, strategyParameters)


def worker_process(strategyClass, port):
    class Worker(worker.Worker):
        def runStrategy(self, barFeed, *args, **kwargs):
            strat = strategyClass(barFeed, *args, **kwargs)
            strat.run()
            return strat.getResult()

    # Create a worker and run it.
    name = "worker-%s" % (os.getpid())
    w = Worker("localhost", port, name)
    w.getLogger().setLevel(logging.ERROR)
    w.run()


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


def run(strategyClass, barFeed, strategyParameters, workerCount=None):
    """Executes many instances of a strategy in parallel and finds the parameters that yield the best results.

    :param strategyClass: The strategy class.
    :param barFeed: The bar feed to use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is a tuple that holds parameter values**.
    :param workerCount: The number of strategies to run in parallel. If None then as many workers as CPUs are used.
    :type workerCount: int.
    """

    assert(workerCount is None or workerCount > 0)
    if workerCount is None:
        workerCount = multiprocessing.cpu_count()

    workers = []
    port = find_port()
    if port is None:
        raise Exception("Failed to find a port to listen")

    # Build and start the server thread before the worker processes. We'll manually stop the server once workers have finished.
    srv = server.Server("localhost", port, False)
    serverThread = threading.Thread(target=server_thread, args=(srv, barFeed, strategyParameters, port))
    serverThread.start()

    try:
        # Build the worker processes.
        for i in range(workerCount):
            workers.append(multiprocessing.Process(target=worker_process, args=(strategyClass, port)))

        # Start workers
        for process in workers:
            process.start()

        # Wait workers
        for process in workers:
            process.join()

    finally:
        # Stop and wait the server to finish.
        srv.stop()
        serverThread.join()
