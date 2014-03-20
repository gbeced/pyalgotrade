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
import webapp2

# The usertasks import is necesary for tasks.WorkerTask.fromPickleString to work.
import usertasks
from chanchero import tasks
from chanchero import config


class WorkerTaskHandler(webapp2.RequestHandler):
    def post(self):
        workerTask = tasks.WorkerTask.fromPickleString(self.request.get("workertask"))
        workerTask.run()


def main():
    app = webapp2.WSGIApplication([(config.worker_task_url, WorkerTaskHandler)], debug=True)
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
