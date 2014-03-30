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

import persistence
import strategyexecutor
import chanchero.tasks
from common import logger
from common import timer
from common import parameters

import copy
import traceback

# This is global to reuse previously loaded bars.
strategyExecutor = strategyexecutor.StrategyExecutor()


# Build a parameters.ParametersIterator from a StratExecConfig.
def build_params_iterator(stratExecConfig):
    ret = parameters.ParametersIterator(len(stratExecConfig.parameterRanges) / 2)
    for i in range(0, len(stratExecConfig.parameterRanges), 2):
        paramPos = int(i/2)
        firstValue = stratExecConfig.parameterRanges[i]
        lastValue = stratExecConfig.parameterRanges[i+1]
        ret.setRange(paramPos, firstValue, lastValue)
    return ret


class MasterTask(chanchero.tasks.MasterTask):
    def __init__(self, taskId, stratExecConfig):
        chanchero.tasks.MasterTask.__init__(self, taskId)
        # Everything that is defined here should be pickleable or reset in beforeToPickleString.
        self.__stratExecConfigKey = stratExecConfig.key()
        self.__paramsIt = build_params_iterator(stratExecConfig)
        self.__tooManyErrosChecked = False
        self.__logger = logger.Logger()

    def beforeToPickleString(self):
        # Reset to avoid from getting pickled.
        self.__tooManyErrosChecked = False

    def isFinished(self):
        return self.__paramsIt.getCurrent() is None

    def getNextWorker(self):
        # Check if we need to abort executions.
        # We're doing this only once per MasterTask execution to avoid calling the db too much.
        if not self.__tooManyErrosChecked:
            self.__tooManyErrosChecked = True
            stratExecConfig = persistence.StratExecConfig.getByKey(self.__stratExecConfigKey)
            if stratExecConfig.status == persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS:
                self.__logger.error("Dropping execution of '%s' due to too many errors" % (stratExecConfig.className))
                return None

        chunkSize = 1000  # Max executions per task.
        ret = None
        if not self.isFinished():
            # Clone self.__paramsIt before building WorkerTask because we'll modify it immediately.
            paramsIt = copy.deepcopy(self.__paramsIt)
            ret = WorkerTask(1, self.__stratExecConfigKey, paramsIt, chunkSize)

            # Advance parameters iterator for the next worker.
            for i in xrange(chunkSize):
                self.__paramsIt.moveNext()
        return ret


class WorkerTask(chanchero.tasks.WorkerTask):
    def __init__(self, taskId, stratExecConfigKey, paramsIt, chunkSize):
        chanchero.tasks.WorkerTask.__init__(self, taskId)
        # Everything that is defined here should be pickleable or reset in beforeToPickleString.
        self.__stratExecConfigKey = stratExecConfigKey
        self.__paramsIt = paramsIt
        self.__chunkSize = chunkSize
        self.__logger = logger.Logger()

    def run(self):
        global strategyExecutor

        taskTimer = timer.Timer()
        stratExecConfig = persistence.StratExecConfig.getByKey(self.__stratExecConfigKey)
        self.__logger.info("WorkerTask for '%s' starting from %s" % (stratExecConfig.className, str(self.__paramsIt.getCurrent())))

        maxTaskRunTime = 9 * 60  # Stop the task after 9 minutes to avoid getting interrupted after 10 minutes.
        bestResult = 0.0
        bestResultParams = []
        errors = 0
        executions = 0
        maxStratTime = 0

        while self.__chunkSize > 0:
            stratExecTimer = timer.Timer()
            try:
                paramValues = self.__paramsIt.getCurrent()
                # self.__logger.info("WorkerTask running '%s' with parameters: %s" % (stratExecConfig.className, paramValues))

                # If there are no more parameters, just stop.
                if paramValues is None:
                    break

                result = strategyExecutor.runStrategy(stratExecConfig, paramValues)
                if result > bestResult:
                    bestResult = result
                    bestResultParams = paramValues
            except Exception, e:
                errors += 1
                strategyExecutor.getLogger().error("Error executing strategy '%s' with parameters %s: %s" % (stratExecConfig.className, paramValues, e))
                strategyExecutor.getLogger().error(traceback.format_exc())

            maxStratTime = max(maxStratTime, stratExecTimer.secondsElapsed())
            executions += 1
            self.__chunkSize -= 1
            self.__paramsIt.moveNext()

            # Stop executing if we'll ran out of time with the next execution.
            if self.__chunkSize > 0 and taskTimer.secondsElapsed() + maxStratTime > maxTaskRunTime:
                break

        # Save the (potentially partial) results.
        ResultTask(1, self.__stratExecConfigKey, bestResult, bestResultParams, executions, errors).queue()

        # Reschedule ourselves if there is work left to do.
        if self.__chunkSize > 0 and self.__paramsIt.getCurrent() is not None:
            self.__logger.info("Rescheduling WorkerTask for '%s' after %d minutes. %d executions completed. Continuing from %s." % (stratExecConfig.className, taskTimer.minutesElapsed(), executions, self.__paramsIt.getCurrent()))
            self.queue()
        else:
            self.__logger.info("WorkerTask for '%s' finished after %d minutes. %d executions completed. Max strat runtime %d seconds." % (stratExecConfig.className, taskTimer.minutesElapsed(), executions, maxStratTime))


class ResultTask(chanchero.tasks.ResultTask):
    def __init__(self, taskId, stratExecConfigKey, result, paramValues, executions, errors):
        chanchero.tasks.ResultTask.__init__(self, taskId)
        # Everything that is defined here should be pickleable or reset in beforeToPickleString.
        self.__stratExecConfigKey = stratExecConfigKey
        self.__result = result
        self.__paramValues = paramValues
        self.__executions = executions
        self.__errors = errors

    def run(self):
        stratExecConfig = persistence.StratExecConfig.getByKey(self.__stratExecConfigKey)

        # Update best result.
        if stratExecConfig.bestResult is None or self.__result > stratExecConfig.bestResult:
            # Need to convert paramValues to a list before storing that.
            paramValues = [value for value in self.__paramValues]
            stratExecConfig.bestResult = self.__result
            stratExecConfig.bestResultParameters = paramValues

        stratExecConfig.executionsFinished += self.__executions
        stratExecConfig.errors += self.__errors
        if stratExecConfig.executionsFinished == stratExecConfig.totalExecutions:
            stratExecConfig.status = persistence.StratExecConfig.Status.FINISHED
        # If we got more that 1000 errors, cancel the strategy execution to avoid wasting resources.
        elif stratExecConfig.errors > 1000:
            stratExecConfig.status = persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS

        stratExecConfig.put()
