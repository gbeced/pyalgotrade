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

import zmq
import threading
import time

class OptimizationManager(threading.Thread):

    jobSubmitSocket = None
    jobRequestsSocket = None
    resultsSocket = None
    zmqContext = zmq.Context.instance()
    _started = True

    def __init__(self, 
    jobSubmitHost = "127.0.0.1", jobSbmitPort = 5000,
    jobRequestsHost = "127.0.0.1", jobRequestsPort = 5001, 
    resultsHost = "127.0.0.1", resultsPort = 5002 ):
        super(OptimizationManager,self).__init__(
            group=None, name="OptimizationManager")
        self.jobSubmitSocket = self.zmqContext.socket(zmq.REQ)
        self.jobSubmitSocket.bind("tcp://"+str(jobSubmitHost)+":"+str(jobSbmitPort))
        self.jobRequestsSocket = self.zmqContext.socket(zmq.REQ)
        self.jobRequestsSocket.bind("tcp://"+str(jobRequestsHost)+":"+str(jobRequestsPort))
        self.resultsSocket = self.zmqContext.socket(zmq.SUB)
        self.resultsSocket.bind("tcp://"+str(resultsHost)+":"+str(resultsPort))

    def __enter__(self):
        return self

    def _shutdown(self):
        if self.jobSUbmitSocket is not None:
            self.jobSubmitSocket.close()
            self.jobSubmitSocket = None
        if self.jobRequestsSocket is not None:
            self.jobRequestsSocket.close()
            self.jobRequestsSocket = None
        if self.resultsSocket is not None:
            self.jobRequestsSocket.close()
            self.jobRequestsSocket = None

    def __exit__(self, exc_type, exc_value, traceback):
        self._shutdown()

    def run(self):
        while self._started:
            time.sleep(100)
            pass
        
    def stop(self):
        self._started = False

if __name__ == '__main__':
    manager = OptimizationManager()
    manager.start()
