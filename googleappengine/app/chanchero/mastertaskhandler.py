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

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import taskqueue
import webapp2

# The usertasks import is necesary for tasks.MasterTask.fromPickleString to work.
import usertasks
from chanchero import tasks
from chanchero import config


class MasterTaskHandler(webapp2.RequestHandler):
    def post(self):
        masterTask = tasks.MasterTask.fromPickleString(self.request.get("mastertask"))
        maxWorkerTasksQueued = 500

        # Get the number of tasks in the worker task queue.
        stats = taskqueue.Queue(config.worker_task_queue).fetch_statistics()
        maxWorkerTasksQueued -= stats.tasks

        # Build worker tasks from the master task.
        while not masterTask.isFinished() and maxWorkerTasksQueued > 0:
            nextWorkerTask = masterTask.getNextWorker()
            if nextWorkerTask is not None:
                maxWorkerTasksQueued -= 1
                nextWorkerTask.queue()

        # If the master task was not fully expanded, queue it again.
        if not masterTask.isFinished():
            masterTask.queue()


def main():
    app = webapp2.WSGIApplication([(config.master_task_url, MasterTaskHandler)], debug=True)
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
