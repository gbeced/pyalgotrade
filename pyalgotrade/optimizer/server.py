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

import pyalgotrade.logger
from pyalgotrade.optimizer import base
from pyalgotrade.optimizer import xmlrpcserver

logger = pyalgotrade.logger.getLogger(__name__)


class Results(object):
    """The results of the strategy executions."""
    def __init__(self, parameters, result):
        self.__parameters = parameters
        self.__result = result

    def getParameters(self):
        """Returns a sequence of parameter values."""
        return self.__parameters

    def getResult(self):
        """Returns the result for a given set of parameters."""
        return self.__result


def startServer(barFeed, strategyParameters, address, port, resultSincFactory, batchSize=200):
    """Start a server and distribute jobs to workers.

    :param barFeed: The bar feed that each worker will use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is a tuple that holds parameter values**.
    :param address: The address to listen for incoming worker connections.
    :type address: string.
    :param port: The port to listen for incoming worker connections.
    :type port: int.
    :param resultSincFactory: The factory which will generate the object to summarize all strategy results.
    :type resultSincFactory: :class:`pyalgotrade.optimizer.base.ResultSincFactory`.
    :param batchSize: The number of strategy executions that are delivered to each worker.
    :type batchSize: int.
    :rtype: The :class:`ResultSinc` object that is created by resultSincFactory to holds the final result.
    """
    paramSource = base.ParameterSource(strategyParameters)
    resultSinc = resultSincFactory.create()
    s = xmlrpcserver.Server(paramSource, resultSinc, barFeed, address, port, batchSize=batchSize)
    logger.info("Starting server")
    s.serve()
    logger.info("Server finished")
    return resultSinc


def serve(barFeed, strategyParameters, address, port, batchSize=200):
    """Executes a server that will provide bars and strategy parameters for workers to use.

    :param barFeed: The bar feed that each worker will use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is a tuple that holds parameter values**.
    :param address: The address to listen for incoming worker connections.
    :type address: string.
    :param port: The port to listen for incoming worker connections.
    :type port: int.
    :param batchSize: The number of strategy executions that are delivered to each worker.
    :type batchSize: int.
    :rtype: A :class:`Results` instance with the best results found or None if no results were obtained.
    """
    ret = None
    factory = base.BestResultFactory()
    resultSinc = startServer(barFeed, strategyParameters, address, port, factory, batchSize=batchSize)
    bestResult, bestParameters = resultSinc.getBest()
    if bestResult is not None:
        logger.info("Best final result %s with parameters %s" % (bestResult, bestParameters.args))
        ret = Results(bestParameters.args, bestResult)
    else:
        logger.error("No results. All jobs failed or no jobs were processed.")
    return ret
