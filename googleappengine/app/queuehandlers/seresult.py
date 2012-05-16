# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

import pickle

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import taskqueue

import persistence

class SEResultHandler(webapp.RequestHandler):
	url = "/queue/seresult"
	class Params:
		stratExecConfigKeyParam = 'stratExecConfigKey'
		resultParam = 'result'
		valuesParam = 'paramValues'
		executionsParam = 'executions'
		errorsParam = 'errors'

	@staticmethod
	def queue(stratExecConfigKey, result, paramValues, executions, errors):
		params = {}
		params[SEResultHandler.Params.stratExecConfigKeyParam] = stratExecConfigKey
		params[SEResultHandler.Params.resultParam] = result
		params[SEResultHandler.Params.valuesParam] = pickle.dumps(paramValues)
		params[SEResultHandler.Params.executionsParam] = executions
		params[SEResultHandler.Params.errorsParam] = errors
		taskqueue.add(queue_name="se-result-queue", url=SEResultHandler.url, params=params)

	def post(self):
		stratExecConfigKey = self.request.get(SEResultHandler.Params.stratExecConfigKeyParam)
		result = float(self.request.get(SEResultHandler.Params.resultParam))
		paramValues = pickle.loads(str(self.request.get(SEResultHandler.Params.valuesParam)))
		executions = int(self.request.get(SEResultHandler.Params.executionsParam))
		errors = int(self.request.get(SEResultHandler.Params.errorsParam))
		stratExecConfig = persistence.StratExecConfig.getByKey(stratExecConfigKey)

		# Update best result.
		if stratExecConfig.bestResult == None or result > stratExecConfig.bestResult:
			# Need to convert paramValues to a list before storing that.
			paramValues = [value for value in paramValues]
			stratExecConfig.bestResult = result
			stratExecConfig.bestResultParameters = paramValues

		stratExecConfig.executionsFinished += executions
		stratExecConfig.errors += errors
		if stratExecConfig.executionsFinished == stratExecConfig.totalExecutions:
			stratExecConfig.status = persistence.StratExecConfig.Status.FINISHED
		# If we got more that 1000 errors, cancel the strategy execution to avoid wasting resources.
		elif stratExecConfig.errors > 1000:
			stratExecConfig.status = persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS

		stratExecConfig.put()

def main():
	application = webapp.WSGIApplication([(SEResultHandler.url, SEResultHandler)], debug=True)
	run_wsgi_app(application)

if __name__ == "__main__":
	main()

