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

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import taskqueue
from google.appengine.api import memcache

import pickle
import zlib
import traceback

from pyalgotrade.barfeed import helpers
from pyalgotrade import barfeed
from pyalgotrade import bar
import persistence
from queuehandlers import seresult
from common import cls
from common import timer
import common.logger

# Converts a persistence.Bar to a pyalgotrade.bar.Bar.
def ds_bar_to_pyalgotrade_bar(dsBar):
	return bar.Bar(dsBar.dateTime, dsBar.open_, dsBar.high, dsBar.low, dsBar.close_, dsBar.volume, dsBar.adjClose)

# Loads pyalgotrade.bar.Bar objects from the db.
def load_pyalgotrade_daily_bars(instrument, barType, fromDateTime, toDateTime):
	ret = []
	dbBars = persistence.Bar.getBars(instrument, barType, fromDateTime, toDateTime)
	for dbBar in dbBars:
		ret.append(ds_bar_to_pyalgotrade_bar(dbBar))
	helpers.set_session_close_attributes(ret)
	return ret

class BarFeed(barfeed.BarFeed):
	def __init__(self, instrument, barSequence):
		barfeed.BarFeed.__init__(self)
		self.__instrument = instrument
		self.registerInstrument(instrument)
		self.__barIter = iter(barSequence)
		self.__stopDispatching = False

	def start(self):
		pass

	def stop(self):
		pass

	def join(self):
		pass

	def fetchNextBars(self):
		ret = None
		try:
			ret = {self.__instrument : self.__barIter.next()}
		except StopIteration:
			self.__stopDispatching = True
		return ret

	def stopDispatching(self):
		return self.__stopDispatching

class BarsCache:
	def __init__(self, logger):
		self.__cache = {}
		self.__logger = logger

	def __addLocal(self, key, bars):
		self.__cache[key] = bars

	def __getLocal(self, key):
		return self.__cache.get(key, None)

	def __addToMemCache(self, key, bars):
		try:
			value = str(pickle.dumps(bars))
			value = zlib.compress(value, 9)
			memcache.add(key=key, value=value)
		except Exception, e:
			self.__logger.error("Failed to add bars to memcache: %s" % e)

	def __getFromMemCache(self, key):
		ret = None
		try:
			value = memcache.get(key)
			if value != None:
				value = zlib.decompress(value)
				ret = pickle.loads(value)
		except Exception, e:
			self.__logger.error("Failed to load bars from memcache: %s" % e)
		return ret

	def add(self, key, bars):
		key = str(key)
		self.__addLocal(key, bars)
		self.__addToMemCache(key, bars)

	def get(self, key):
		key = str(key)
		ret = self.__getLocal(key)
		if ret == None:
			ret = self.__getFromMemCache(key)
			if ret != None:
				# Store in local cache for later use.
				self.__addLocal(key, ret)
		return ret

class StrategyExecutor:
	def __init__(self):
		self.__logger = common.logger.Logger()
		self.__barCache = BarsCache(self.__logger)

	def __loadBars(self, stratExecConfig):
		ret = self.__barCache.get(stratExecConfig.key())
		if ret == None:
			self.__logger.info("Loading '%s' bars from %s to %s" % (stratExecConfig.instrument, stratExecConfig.firstDate, stratExecConfig.lastDate))
			ret = load_pyalgotrade_daily_bars(stratExecConfig.instrument, stratExecConfig.barType, stratExecConfig.firstDate, stratExecConfig.lastDate)
			self.__barCache.add(stratExecConfig.key(), ret)
		return ret

	def getLogger(self):
		return self.__logger

	def runStrategy(self, stratExecConfig, paramValues):
		bars = self.__loadBars(stratExecConfig)
		barFeed = BarFeed(stratExecConfig.instrument, bars)

		# Evaluate the strategy with the feed bars.
		params = [barFeed]
		params.extend(paramValues)
		myStrategy = cls.Class(stratExecConfig.className).getClass()(*params)
		myStrategy.run()
		return myStrategy.getResult()

class SEConsumerHandler(webapp.RequestHandler):
	url = "/queue/seconsumer"
	defaultBatchSize = 200

	class Params:
		stratExecConfigKeyParam = 'stratExecConfigKey'
		paramsItParam = 'paramsIt'
		batchSizeParam = 'batchSize'

	@staticmethod
	def queue(stratExecConfigKey, paramsIt, batchSize):
		params = {}
		params[SEConsumerHandler.Params.stratExecConfigKeyParam] = stratExecConfigKey
		params[SEConsumerHandler.Params.paramsItParam] = pickle.dumps(paramsIt)
		params[SEConsumerHandler.Params.batchSizeParam] = batchSize
		taskqueue.add(queue_name="se-consumer-queue", url=SEConsumerHandler.url, params=params)

	def post(self):
		global strategyExecutor

		tmr = timer.Timer()
		stratExecConfigKey = self.request.get(SEConsumerHandler.Params.stratExecConfigKeyParam)
		paramsIt = pickle.loads(str(self.request.get(SEConsumerHandler.Params.paramsItParam)))
		batchSize = int(self.request.get(SEConsumerHandler.Params.batchSizeParam))
		stratExecConfig = persistence.StratExecConfig.getByKey(stratExecConfigKey)

		bestResult = 0
		bestResultParams = []
		executionsLeft = batchSize 
		errors = 0 
		while executionsLeft > 0:
			try:
				paramValues = paramsIt.getCurrent()

				# If there are no more parameters, just stop.
				if paramValues == None:
					break

				result = strategyExecutor.runStrategy(stratExecConfig, paramValues)
				if result > bestResult:
					bestResult = result
					bestResultParams = paramValues
			except Exception, e:
				errors += 1
				strategyExecutor.getLogger().error("Error executing strategy '%s' with parameters %s: %s" % (stratExecConfig.className, paramValues, e))
				strategyExecutor.getLogger().error(traceback.format_exc())

			executionsLeft -= 1
			paramsIt.moveNext()

			# Stop executing before we ran out of time. I'm assuming that strategies take less than 1 minute to execute.
			if tmr.minutesElapsed() > 9 and executionsLeft > 0:
				strategyExecutor.getLogger().info("Rescheduling. %d executions left." % executionsLeft)
				SEConsumerHandler.queue(stratExecConfigKey, paramsIt, executionsLeft)
				break

		# Queue the results.
		seresult.SEResultHandler.queue(stratExecConfigKey, bestResult, bestResultParams, batchSize - executionsLeft, errors)

# This is global to reuse previously loaded bars.
strategyExecutor = StrategyExecutor()

def main():
	_handlers = [
			(SEConsumerHandler.url, SEConsumerHandler)
			]
	application = webapp.WSGIApplication(_handlers, debug=True)
	run_wsgi_app(application)

if __name__ == "__main__":
	main()

