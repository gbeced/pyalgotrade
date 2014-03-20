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

import os

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import pages.strategy
import strategies
import persistence


class HomePage(webapp.RequestHandler):
    url = "/"

    def get(self):
        templateValues = {}
        templateValues["logout_url"] = users.create_logout_url("/")
        templateValues["user"] = users.get_current_user()
        templateValues["strategies"] = []

        for strategyClass in strategies.get_strategy_classes():
            strategyValues = {}
            strategyValues["class"] = strategyClass
            strategyValues["url"] = pages.strategy.StrategyPage.getUrl(strategyClass)
            templateValues["strategies"].append(strategyValues)

        templateValues["active_executions"] = pages.strategy.get_stratexecconfig_for_template(persistence.StratExecConfig.getByStatus([persistence.StratExecConfig.Status.ACTIVE]))

        path = os.path.join(os.path.dirname(__file__), "..", "templates", 'index.html')
        self.response.out.write(template.render(path, templateValues))


def main():
    application = webapp.WSGIApplication([(HomePage.url, HomePage)], debug=True)
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
