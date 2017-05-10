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
    """Optimization manager: receives jobs from submitters, distributes them
    to workers.

    This is intended as a centralized manager (orchestrator) of the
    optimization process. It will accept a certain batch from a client
    (strategy, data and a parameter "table") then distribute each job to any
    worker that requests one. Results will be stored locally for further
    consumption by the clients.
    """

    # Interaction with submitters
    clientRequestSocket = None
    clientReplySocket = None

    # Interaction with workers
    workerRequestSocket = None
    resultsSubmitSocket = None

    poller = None

    zmqContext = zmq.Context.instance()

    def __init__(self,
                 clientIfAddr="127.0.0.1", clientRequestPort=5000, 
                 clientReplyPort=5001,
                 workerIfAddr="127.0.0.1", workerRequestPort=5002, 
                 workerReplyPort=5003):
        super(OptimizationManager, self).__init__(
            group=None, name="OptimizationManager")

        # This should really be replaced with the new CLIENT-SERVER socket
        # model available in later iterations of ZMQ

        # "Servers" (submitters) interface
        self.clientRequestSocket = self.zmqContext.socket(zmq.SUB)
        self.clientRequestSocket.bind(
            "tcp://" + str(clientIfAddr) + ":" + str(clientRequestPort))
        self.clientRequestSocket.subscribe("")
        self.clientReplySocket = self.zmqContext.socket(zmq.PUB)
        self.clientReplySocket.bind(
            "tcp://" + str(clientIfAddr) + ":" + str(clientReplyPort))

        # Workers interface
        self.workerRequestSocket = self.zmqContext.socket(zmq.SUB)
        self.workerRequestSocket.bind(
            "tcp://" + str(workerIfAddr) + ":" + str(workerRequestPort))
        self.workerRequestSocket.subscribe("")
        self.workerReplySocket = self.zmqContext.socket(zmq.PUB)
        self.workerReplySocket.bind(
            "tcp://" + str(workerIfAddr) + ":" + str(workerReplyPort))

        self.poller = zmq.Poller()
        self.poller.register(self.clientRequestSocket, zmq.POLLIN)
        self.poller.register(self.workerRequestSocket, zmq.POLLIN)

    def __enter__(self):
        return self

    def _shutdown(self):
        if self.clientRequestSocket is not None:
            self.clientRequestSocket.close()
            self.clientRequestSocket = None
        if self.workerRequestSocket is not None:
            self.workerRequestSocket.close()
            self.workerRequestSocket = None
        if self.clientReplySocket is not None:
            self.workerRequestSocket.close()
            self.workerRequestSocket = None

    def __exit__(self, exc_type, exc_value, traceback):
        self._shutdown()

    def processClientRequest(self, topicFrame, paramsFrame):
        # topic = str(topicFrame.buffer)
        # params = json.loads(str(paramsFrame.buffer))
        print("Client request: {}, {}".format(
              str(topicFrame), str(paramsFrame)))

    def processWorkerRequest(self, topicFrame, paramsFrame):
        # topic = str(topicFrame.buffer)
        # params = json.loads(str(paramsFrame.buffer))
        print("Worker request: {}, {}".format(
              str(topicFrame), str(paramsFrame)))

    def run(self):
        print("OptimizationManager running")

        while self.doRun:
            # Poll on a timer so that we can regularly
            # check the loop condition
            events = dict(self.poller.poll(1000))

            print("len(events): {}".format(len(events)))
            if len(events) == 0:
                continue

            # This will process one message from each socket
            # per iteration (if available)
            if self.clientRequestSocket in events:
                print("Client Request")
                frames = self.clientRequestSocket.recv_multipart()
                if len(frames) < 2:
                    raise Exception("Client request too short")
                elif len(frames) > 2:
                    raise Exception("Client request too long")
                topic = frames.pop(0)
                params = frames.pop(0)
                self.processClientRequest(topic, params)
            if self.workerRequestSocket in events:
                print("Worker Request")
                frames = self.workerRequestSocket.recv_multipart()
                if len(frames) < 2:
                    raise Exception("Worker request too short")
                elif len(frames) > 2:
                    raise Exception("Worker request too long")
                topic = frames.pop([0])
                params = frames.pop([0])
                self.processWorkerRequest(topic, params)

    def stop(self):
        self.doRun = False


if __name__ == '__main__':
    manager = OptimizationManager()
    manager.doRun = True
    manager.start()
