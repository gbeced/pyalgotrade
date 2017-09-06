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

import SimpleXMLRPCServer
import pickle
import threading
import time

import pyalgotrade.logger
from pyalgotrade.optimizer import base

logger = pyalgotrade.logger.getLogger(__name__)


class AutoStopThread(threading.Thread):
    """A separate thread which helps server monitor jobs' status and stops server when jobs finished"""
    def __init__(self, server):
        super(AutoStopThread, self).__init__()
        self.__server = server

    def run(self):
        while self.__server.jobsPending():
            time.sleep(1)
        self.__server.stop()


class Job(object):
    """Represents a job to be given to a worker."""
    def __init__(self, strategyParameters):
        """
        :param paramSource: The list of parameters to be given to a worker to run with.
        :type paramSource: A list of :class:`pyalgotrade.optimizer.base.Parameters`
        """
        self.__strategyParameters = strategyParameters
        self.__id = id(self)

    def getId(self):
        return self.__id

    def getNextParameters(self):
        ret = None
        if len(self.__strategyParameters):
            ret = self.__strategyParameters.pop()
        return ret


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    rpc_paths = ('/PyAlgoTradeRPC',)


class Server(SimpleXMLRPCServer.SimpleXMLRPCServer):
    def __init__(self, paramSource, resultSinc, barFeed, address, port, autoStop=True, batchSize=200):
        """
        :param paramSource: All parameters to be distributed to workers.
        :type paramSource: :class:`pyalgotrade.optimizer.base.ParameterSource`
        :param resultSinc: The object to hold the worker results. It does not need to be thread safe.
        :type resultSinc: :class:`pyalgotrade.optimizer.base.ResultSinc`
        :param barFeed: The market data to be sent to worker.
        :type barFeed: :class:`pyalgotrade.barfeed.BaseBarFeed`
        :param address: The address to be used as server.
        :type address: str
        :param port: The server port.
        :type port: int
        :param autoStop: Wheather automatically stop this server after finishing all jobs.
        :type autoStop: bool
        :param batchSize: The number of parameters which workers will take and process on each transmission.
        :type batchSize: int
        """
        assert batchSize > 0, "Invalid batch size"

        SimpleXMLRPCServer.SimpleXMLRPCServer.__init__(self, (address, port), requestHandler=RequestHandler, logRequests=False, allow_none=True)
        self.__batchSize = batchSize
        self.__paramSource = paramSource
        self.__resultSinc = resultSinc
        self.__resultSincLock = threading.Lock()
        self.__barFeed = barFeed
        self.__instrumentsAndBars = None  # Pickle'd instruments and bars for faster retrieval.
        self.__barsFreq = None
        self.__activeJobs = {}
        self.__activeJobsLock = threading.Lock()
        self.__forcedStop = False
        if autoStop:
            self.__autoStopThread = AutoStopThread(self)
        else:
            self.__autoStopThread = None

        self.register_introspection_functions()
        self.register_function(self.getInstrumentsAndBars, 'getInstrumentsAndBars')
        self.register_function(self.getBarsFrequency, 'getBarsFrequency')
        self.register_function(self.getNextJob, 'getNextJob')
        self.register_function(self.pushJobResults, 'pushJobResults')

    def getInstrumentsAndBars(self):
        return self.__instrumentsAndBars

    def getBarsFrequency(self):
        return str(self.__barsFreq)

    def getNextJob(self):
        ret = None

        with self.__activeJobsLock:
            # Get the next set of parameters.
            params = self.__paramSource.getNext(self.__batchSize)

            # Map the active job
            if len(params):
                ret = Job(params)
                self.__activeJobs[ret.getId()] = ret

        return pickle.dumps(ret)

    def jobsPending(self):
        if self.__forcedStop:
            return False

        with self.__activeJobsLock:
            jobsPending = not self.__paramSource.eof()
            activeJobs = len(self.__activeJobs) > 0

        return jobsPending or activeJobs

    def pushJobResults(self, jobId, resultSinc, workerName):
        jobId = pickle.loads(jobId)
        resultSinc = pickle.loads(resultSinc)

        # Remove the job mapping.
        with self.__activeJobsLock:
            try:
                del self.__activeJobs[jobId]
            except KeyError:
                # The job's results were already submitted.
                return

        with self.__resultSincLock:
            self.__resultSinc.pushResultSinc(resultSinc)

    def stop(self):
        self.shutdown()

    def serve(self):
        try:
            # Initialize instruments, bars and parameters.
            logger.info("Loading bars")
            loadedBars = []
            for dateTime, bars in self.__barFeed:
                loadedBars.append(bars)
            instruments = self.__barFeed.getRegisteredInstruments()
            self.__instrumentsAndBars = pickle.dumps((instruments, loadedBars))
            self.__barsFreq = self.__barFeed.getFrequency()

            if self.__autoStopThread:
                self.__autoStopThread.start()

            logger.info("Started serving")
            self.serve_forever()
            logger.info("Finished serving")

            if self.__autoStopThread:
                self.__autoStopThread.join()
        finally:
            self.__forcedStop = True
