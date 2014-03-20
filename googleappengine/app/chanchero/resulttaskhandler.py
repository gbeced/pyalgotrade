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

# The usertasks import is necesary for tasks.ResultTask.fromPickleString to work.
import usertasks
from chanchero import tasks
from chanchero import config


class ResultTaskHandler(webapp2.RequestHandler):
    def post(self):
        resultTask = tasks.ResultTask.fromPickleString(self.request.get("resulttask"))
        resultTask.run()


def main():
    app = webapp2.WSGIApplication([(config.result_task_url, ResultTaskHandler)], debug=True)
    run_wsgi_app(app)


if __name__ == "__main__":
    main()
