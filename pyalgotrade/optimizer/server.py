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

import threading

import pyalgotrade.logger
from pyalgotrade.optimizer import base
from pyalgotrade.optimizer import xmlrpcserver

logger = pyalgotrade.logger.getLogger(__name__)


######################################################################


class ParameterSource(object):
    """
    Source for backtesting parameters. This class is thread safe.
    """
    def __init__(self, params):
        self.__iter = iter(params)
        self.__lock = threading.Lock()

    def getNext(self, count):
        """
        Returns the next parameters to use in a backtest.
        If there are no more parameters to try then an empty list is returned.

        :param count: The max number of parameters to return.
        :type count: int
        :rtype: list of Parameters.
        """

        assert count > 0, "Invalid number of parameters"

        ret = []
        with self.__lock:
            if self.__iter is not None:
                try:
                    while count > 0:
                        params = self.__iter.next()
                        # Backward compatibility when parameters don't yield base.Parameters.
                        if not isinstance(params, base.Parameters):
                            params = base.Parameters(*params)
                        ret.append(params)
                        count -= 1
                except StopIteration:
                    self.__iter = None
        return ret

    def eof(self):
        with self.__lock:
            return self.__iter is None


class ResultSinc(object):
    """
    Sinc for backtest results. This class is thread safe.
    """
    def __init__(self):
        self.__lock = threading.Lock()
        self.__bestResult = None
        self.__bestParameters = None

    def push(self, result, parameters):
        """
        Push strategy results obtained by running the strategy with the given parameters.

        :param result: The result obtained by running the strategy with the given parameters.
        :type result: float
        :param parameters: The parameters that yield the given result.
        :type parameters: Parameters
        """
        with self.__lock:
            if result is not None and (self.__bestResult is None or result > self.__bestResult):
                self.__bestResult = result
                self.__bestParameters = parameters
                logger.info("Best result so far %s with parameters %s" % (result, parameters.args))

    def getBest(self):
        with self.__lock:
            ret = self.__bestResult, self.__bestParameters
        return ret


######################################################################
######################################################################


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


def serve(barFeed, strategyParameters, address, port):
    """Executes a server that will provide bars and strategy parameters for workers to use.

    :param barFeed: The bar feed that each worker will use to backtest the strategy.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`.
    :param strategyParameters: The set of parameters to use for backtesting. An iterable object where **each element is a tuple that holds parameter values**.
    :param address: The address to listen for incoming worker connections.
    :type address: string.
    :param port: The port to listen for incoming worker connections.
    :type port: int.
    :rtype: A :class:`Results` instance with the best results found or None if no results were obtained.
    """

    paramSource = ParameterSource(strategyParameters)
    resultSinc = ResultSinc()
    s = xmlrpcserver.Server(paramSource, resultSinc, barFeed, address, port)
    logger.info("Starting server")
    s.serve()
    logger.info("Server finished")

    ret = None
    bestResult, bestParameters = resultSinc.getBest()
    if bestResult is not None:
        logger.info("Best final result %s with parameters %s" % (bestResult, bestParameters.args))
        ret = Results(bestParameters.args, bestResult)
    else:
        logger.error("No results. All jobs failed or no jobs were processed.")
    return ret
