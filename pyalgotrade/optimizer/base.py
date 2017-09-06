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

import threading


class Parameters(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "<%s, %s>" % (self.args, self.kwargs)

class ParameterSource(object):
    """
    Source for backtesting parameters. This class is thread safe.
    """
    def __init__(self, params):
        """
        :param params: A list of parameters.
        :type params: a list of :class:`Parameters` object or a list of list
        """
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
                        # Backward compatibility when parameters don't yield Parameters.
                        if not isinstance(params, Parameters):
                            params = Parameters(*params)
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
    Sinc for backtest results.
    """
    def push(self, result, parameters):
        """
        Push strategy results obtained by running the strategy with the given parameters.

        :param result: The result obtained by running the strategy with the given parameters.
        :param parameters: The parameters that yield the given result.
        :type parameters: :class:`pyalgotrade.optimizer.base.Parameters`
        """
        raise Exception("Not implemented")

    def pushResultSinc(self, resultSinc):
        """
        Push the other summary of strategy results.

        :param resultSinc: The same type of object that holds the summary of strategy results.
        :type resultSinc: :class:`pyalgotrade.optimizer.base.ResultSinc`
        """
        raise Exception("Not implemented")


class BestResult(ResultSinc):
    """
    Holds the best strategy result and the respective parameters. This class is thread safe.
    """
    def __init__(self):
        self.__lock = threading.Lock()
        self.__bestResult = None
        self.__bestParameters = None

    def push(self, result, parameters):
        """
        Replace current best strategy result if the new result is greater.

        :param result: The result obtained by running the strategy with the given parameters.
        :type result: float
        :param parameters: The parameters that yield the given result.
        :type parameters: :class:`pyalgotrade.optimizer.base.Parameters`
        """
        with self.__lock:
            self.onNewResult(result, parameters)
            if result is not None and (self.__bestResult is None or result > self.__bestResult):
                self.__bestResult = result
                self.__bestParameters = parameters
                self.onNewBestResult(result, parameters)

    def pushResultSinc(self, resultSinc):
        """
        Replace current best strategy result if the incoming result is greater.

        :param resultSinc: Another best strategy result and parameters.
        :type resultSinc: :class:`pyalgotrade.optimizer.base.BestResult`
        """
        bestResult, bestParameters = resultSinc.getBest()
        self.push(bestResult, bestParameters)

    def getBest(self):
        with self.__lock:
            ret = self.__bestResult, self.__bestParameters
        return ret

    def onNewResult(self, result, parameters):
        pass

    def onNewBestResult(self, result, parameters):
        pass

    def __getstate__(self):
        state = self.__dict__.copy()
        del state['_BestResult__lock']  # remove __lock variable before pickle
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__lock = threading.Lock()


class ResultSincFactory(object):
    """A factory that creates the ResultSinc object."""
    def create(self):
        """Should be inherit to create the object of subclass of ResultSinc."""
        raise Exception("Not implemented")


class BestResultFactory(ResultSincFactory):
    """A factory that creates the BestResult object."""
    def create(self):
        """Create new BestResult object.
        :rtype: :class:`BestResult`
        """
        return BestResult()


class StrategyRunner(object):
    """An executor to run the user-defined strategy and get the result."""
    def runStrategy(self, feed, parameters):
        """Process the given market data and strategy parameters, and generate a result.
        
        :param feed: The market data.
        :type feed: :class:`pyalgotrade.barfeed.BaseBarFeed`
        :param parameters: The parameters for the strategy.
        :type parameters: :class:`pyalgotrade.optimizer.base.Parameters`
        """
        raise Exception("Not implemented")


class AnyStrategyRunner(StrategyRunner):
    """A strategy executor that accept any strategys."""
    def __init__(self, strategyClass):
        """
        :param strategyClass: The subclass of `pyalgotrade.strategy.BacktestingStrategy`.
        :type strategyClass: type
        """
        self.__strategyClass = strategyClass

    def runStrategy(self, feed, parameters):
        """Process the market data and return the final portfolio

        :param feed: The market data.
        :type feed: :class:`pyalgotrade.barfeed.BaseBarFeed`
        :param parameters: The parameters for the strategy.
        :type parameters: :class:`pyalgotrade.optimizer.base.Parameters`
        :rtype: float
        """
        strat = self.__strategyClass(feed, *parameters.args, **parameters.kwargs)
        strat.run()
        return strat.getResult()
