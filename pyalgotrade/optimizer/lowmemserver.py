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

import pyalgotrade.logger
from pyalgotrade.optimizer import base
from pyalgotrade.optimizer import lowmemxmlrpcserver

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


def serveDataAndCode(instsAndDataFilenames, feedPickle, strategyParameters,
                     address, port):

    paramSource = base.ParameterSource(strategyParameters)
    resultSinc = base.ResultSinc()
    s = lowmemxmlrpcserver.LowMemXmlRpcServer(paramSource, resultSinc,
                                              instsAndDataFilenames,
                                              feedPickle, address, port)
    logger.info("Starting server")
    s.serve()
    logger.info("Server finished")

    ret = None
    bestResult, bestParameters = resultSinc.getBest()
    if bestResult is not None:
        logger.info("Best final result %s with parameters %s" %
                    (bestResult, bestParameters.args))
        ret = Results(bestParameters.args, bestResult)
    else:
        logger.error("No results. All jobs failed or no jobs were processed.")
    return ret
