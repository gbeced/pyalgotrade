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
from queuehandlers import seconsumer
from common import parameters
import common.logger

# Build a parameters.ParametersIterator from a StratExecConfig.
def build_params_iterator(stratExecConfig):
	ret = parameters.ParametersIterator(len(stratExecConfig.parameterRanges) / 2)
	for i in range(0, len(stratExecConfig.parameterRanges), 2):
		paramPos = int(i/2)
		firstValue = stratExecConfig.parameterRanges[i]
		lastValue = stratExecConfig.parameterRanges[i+1]
		ret.setRange(paramPos, firstValue, lastValue)
	return ret

class SEProducerHandler(webapp.RequestHandler):
	url = "/queue/seproducer"
	class Params:
		stratExecConfigKeyParam = 'stratExecConfigKey'
		paramsItParam = 'paramsIt'

	@staticmethod
	def queue(stratExecConfigKey, paramsIt=None):
		if paramsIt == None:
			stratExecConfig = persistence.StratExecConfig.getByKey(stratExecConfigKey)
			paramsIt = build_params_iterator(stratExecConfig)

		params = {}
		params[SEProducerHandler.Params.stratExecConfigKeyParam] = stratExecConfigKey
		params[SEProducerHandler.Params.paramsItParam] = pickle.dumps(paramsIt)
		taskqueue.add(queue_name="se-producer-queue", url=SEProducerHandler.url, params=params)

	def post(self):
		stratExecConfigKey = self.request.get(SEProducerHandler.Params.stratExecConfigKeyParam)
		paramsIt = pickle.loads(str(self.request.get(SEProducerHandler.Params.paramsItParam)))

		# Check if we need to abort executions.
		stratExecConfig = persistence.StratExecConfig.getByKey(stratExecConfigKey)
		if stratExecConfig.status == persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS:
			common.logger.Logger().error("Skipping producer task due to too many errors")
			return

		# Queue a strategy execution task.
		seconsumer.SEConsumerHandler.queue(stratExecConfigKey, paramsIt, seconsumer.SEConsumerHandler.defaultBatchSize)

		# Queue the next producer task.
		for i in xrange(seconsumer.SEConsumerHandler.defaultBatchSize):
			paramsIt.moveNext()
		if paramsIt.getCurrent() != None:
			SEProducerHandler.queue(stratExecConfigKey, paramsIt)

def main():
	application = webapp.WSGIApplication([(SEProducerHandler.url, SEProducerHandler)], debug=True)
	run_wsgi_app(application)

if __name__ == "__main__":
	main()

