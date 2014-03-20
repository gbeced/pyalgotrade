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

from google.appengine.api import taskqueue

from chanchero import config

import pickle


class Task:
    def __init__(self, taskId):
        self.__taskId = taskId

    def beforeToPickleString(self):
        pass

    def getTaskId(self):
        return self.__taskId

    def toPickleString(self):
        self.beforeToPickleString()
        return str(pickle.dumps(self))

    @staticmethod
    def fromPickleString(pickledTask):
        return pickle.loads(str(pickledTask))


# Master tasks are responsible for partitioning the problem into smaller pieces, called worker tasks.
class MasterTask(Task):
    def __init__(self, taskId):
        Task.__init__(self, taskId)

    def queue(self):
        params = {}
        params["mastertask"] = self.toPickleString()
        taskqueue.add(queue_name=config.master_task_queue, url=config.master_task_url, params=params)

    def isFinished(self):
        raise NotImplementedError()

    def getNextWorker(self):
        raise NotImplementedError()


class WorkerTask(Task):
    def __init__(self, taskId):
        Task.__init__(self, taskId)

    def queue(self):
        params = {}
        params["workertask"] = self.toPickleString()
        taskqueue.add(queue_name=config.worker_task_queue, url=config.worker_task_url, params=params)

    def run(self):
        raise NotImplementedError()


class ResultTask(Task):
    def __init__(self, taskId):
        Task.__init__(self, taskId)

    def queue(self):
        params = {}
        params["resulttask"] = self.toPickleString()
        taskqueue.add(queue_name=config.result_task_queue, url=config.result_task_url, params=params)

    def run(self):
        raise NotImplementedError()
