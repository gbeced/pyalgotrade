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
import datetime
import cgi

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import persistence
import usertasks
from common import utils
from common import cls
from common import forms


def get_stratexecconfig_for_template(stratExecConfigs):
    ret = []
    for stratExecConfig in stratExecConfigs:
        props = {}
        props["class"] = stratExecConfig.className
        props["created"] = stratExecConfig.created.strftime("%d/%b/%Y %H:%M")
        props["executions_finished"] = stratExecConfig.executionsFinished
        props["total_executions"] = stratExecConfig.totalExecutions
        if stratExecConfig.bestResult:
            props["best_result"] = stratExecConfig.bestResult
            props["best_result_parameters"] = stratExecConfig.bestResultParameters

        if stratExecConfig.status in [persistence.StratExecConfig.Status.ACTIVE, persistence.StratExecConfig.Status.FINISHED]:
            if stratExecConfig.errors > 0:
                props["additional_info"] = "%d errors were found. Take a look at the application logs." % (stratExecConfig.errors)
            if stratExecConfig.status == persistence.StratExecConfig.Status.FINISHED:
                props["reexecute_url"] = StrategyExecutionPage.getReExecuteUrl(stratExecConfig.className, stratExecConfig.key())
        elif stratExecConfig.status == persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS:
            props["additional_info"] = "The strategy execution was cancelled because it generated too many errors."
        else:
            assert(False)  # Invalid state

        ret.append(props)
    return ret


class QueueStrategyExecutionForm(forms.Form):
    beginDateParam = "dateBegin"
    endDateParam = "dateEnd"
    instrumentParam = "instrument"

    def __init__(self, request, strategyParams):
        self.__strategyParams = strategyParams
        fieldNames = []

        # Build field names based on __init__ parameters.
        for strategyParam in strategyParams:
            fieldNames.append(self.getBeginParamName(strategyParam))
            fieldNames.append(self.getEndParamName(strategyParam))

        fieldNames.append(QueueStrategyExecutionForm.beginDateParam)
        fieldNames.append(QueueStrategyExecutionForm.endDateParam)
        fieldNames.append(QueueStrategyExecutionForm.instrumentParam)
        forms.Form.__init__(self, request, fieldNames)

    def getBeginParamName(self, strategyParam):
        return strategyParam+"Begin"

    def getEndParamName(self, strategyParam):
        return strategyParam+"End"

    def getParamAsDateTime(self, paramName):
        return datetime.datetime.strptime(self.getRawValue(paramName).strip(), "%Y/%m/%d")

    def getInstrument(self):
        return self.getRawValue(QueueStrategyExecutionForm.instrumentParam).strip()

    def getParamRange(self, strategyParam):
        beginParamValue = self.getRawValue(self.getBeginParamName(strategyParam)).strip()
        endParamValue = self.getRawValue(self.getEndParamName(strategyParam)).strip()
        return (int(beginParamValue), int(endParamValue))

    def __paramValuesValid(self, strategyParam):
        ret = True
        try:
            beginParamValue, endParamValue = self.getParamRange(strategyParam)
            ret = beginParamValue <= endParamValue
        except Exception:
            ret = False
        return ret

    def validateAllParams(self):
        # Validate strategy params.
        for strategyParam in self.__strategyParams:
            if not self.__paramValuesValid(strategyParam):
                raise Exception("%s values are not valid" % strategyParam)

        # Validate date range params.
        try:
            if self.getParamAsDateTime(QueueStrategyExecutionForm.beginDateParam) >= self.getParamAsDateTime(QueueStrategyExecutionForm.endDateParam):
                raise Exception("Begin date should be before end date.")
        except ValueError:
            raise Exception("Date range values are not valid")

        if len(self.getInstrument()) == 0:
            raise Exception("Instrument is not set")

    def getTemplateValues(self):
        formValues = self.getValuesForTemplate()
        ret = {}

        # Strategy parameter values.
        ret["strategy"] = []
        for strategyParam in self.__strategyParams:
            beginParamName = self.getBeginParamName(strategyParam)
            endParamName = self.getEndParamName(strategyParam)

            paramInfo = {}
            paramInfo["name"] = strategyParam
            paramInfo["beginName"] = beginParamName
            paramInfo["endName"] = endParamName
            paramInfo["beginValue"] = formValues[beginParamName]
            paramInfo["endValue"] = formValues[endParamName]
            ret["strategy"].append(paramInfo)

        # Other values.
        ret[QueueStrategyExecutionForm.instrumentParam] = formValues[QueueStrategyExecutionForm.instrumentParam]

        defDateValue = "YYYY/MM/DD"
        # Begin date.
        if formValues[QueueStrategyExecutionForm.beginDateParam] != "":
            ret[QueueStrategyExecutionForm.beginDateParam] = formValues[QueueStrategyExecutionForm.beginDateParam]
        else:
            ret[QueueStrategyExecutionForm.beginDateParam] = defDateValue
        # End date.
        if formValues[QueueStrategyExecutionForm.endDateParam] != "":
            ret[QueueStrategyExecutionForm.endDateParam] = formValues[QueueStrategyExecutionForm.endDateParam]
        else:
            ret[QueueStrategyExecutionForm.endDateParam] = defDateValue

        return ret

    def loadFromStratExecConfig(self, stratExecConfig):
        # Strategy parameter values.
        for strategyParam in self.__strategyParams:
            try:
                pos = stratExecConfig.parameterNames.index(strategyParam)
                beginPos = pos * 2
                endPos = beginPos + 1
                self.setRawValue(self.getBeginParamName(strategyParam), str(stratExecConfig.parameterRanges[beginPos]))
                self.setRawValue(self.getEndParamName(strategyParam), str(stratExecConfig.parameterRanges[endPos]-1))
            except ValueError:
                pass
                # Parameter not found

        # Other values.
        dateFormat = "%Y/%m/%d"
        self.setRawValue(QueueStrategyExecutionForm.instrumentParam, str(stratExecConfig.instrument))
        self.setRawValue(QueueStrategyExecutionForm.beginDateParam, stratExecConfig.firstDate.strftime(dateFormat))
        self.setRawValue(QueueStrategyExecutionForm.endDateParam, stratExecConfig.lastDate.strftime(dateFormat))


class StrategyPage(webapp.RequestHandler):
    url = "/strategy/"

    @staticmethod
    def getUrl(strategyClassName):
        return utils.build_url(StrategyPage.url, {"class": strategyClassName})

    def get(self):
        templateValues = {}
        strategyClassName = cgi.escape(self.request.get("class")).strip()

        # Try to load the class.
        try:
            cls.Class(strategyClassName)
        except Exception, e:
            templateValues["error"] = "Failed to load strategy '%s': %s" % (strategyClassName, e)
            path = os.path.join(os.path.dirname(__file__), "..", "templates", 'error.html')
            self.response.out.write(template.render(path, templateValues))
            return

        # persistence.StratExecConfig.getByClass(strategyClassName)

        # Template values
        strategyValues = {}
        strategyValues["class"] = strategyClassName
        templateValues["logout_url"] = users.create_logout_url("/")
        templateValues["user"] = users.get_current_user()
        templateValues["strategy"] = strategyValues
        templateValues["queue_execution_url"] = StrategyExecutionPage.getUrl(strategyClassName)

        templateValues["active_executions"] = get_stratexecconfig_for_template(persistence.StratExecConfig.getByClass(strategyClassName, [persistence.StratExecConfig.Status.ACTIVE]))
        templateValues["finished_executions"] = get_stratexecconfig_for_template(persistence.StratExecConfig.getByClass(strategyClassName, [persistence.StratExecConfig.Status.FINISHED, persistence.StratExecConfig.Status.CANCELED_TOO_MANY_ERRORS]))

        # Build the response using the template.
        path = os.path.join(os.path.dirname(__file__), "..", "templates", 'strategy.html')
        self.response.out.write(template.render(path, templateValues))


class StrategyExecutionPage(webapp.RequestHandler):
    url = "/strategy/queue_execution/"

    @staticmethod
    def getUrl(strategyClassName):
        return utils.build_url(StrategyExecutionPage.url, {"class": strategyClassName})

    @staticmethod
    def getReExecuteUrl(strategyClassName, stratExecConfigKey):
        return utils.build_url(StrategyExecutionPage.url, {
            "class": strategyClassName,
            "key": stratExecConfigKey
            })

    def __buildStratExecConfig(self, className, strategyParams, form):
        totalExecutions = 1
        parameterRanges = []
        for strategyParam in strategyParams:
            beginParamValue, endParamValue = form.getParamRange(strategyParam)
            endParamValue += 1
            parameterRanges.append(beginParamValue)
            parameterRanges.append(endParamValue)
            totalExecutions *= (endParamValue - beginParamValue)

        ret = persistence.StratExecConfig(
            className=className,
            instrument=form.getInstrument(),
            barType=persistence.Bar.Type.DAILY,
            firstDate=form.getParamAsDateTime(QueueStrategyExecutionForm.beginDateParam),
            lastDate=form.getParamAsDateTime(QueueStrategyExecutionForm.endDateParam),
            parameterNames=strategyParams,
            parameterRanges=parameterRanges,
            created=datetime.datetime.now(),
            status=persistence.StratExecConfig.Status.ACTIVE,
            totalExecutions=totalExecutions
            )

        return ret

    def __handleRequest(self, isPost):
        templateValues = {}
        strategyClassName = cgi.escape(self.request.get("class"))
        stratExecConfigKey = cgi.escape(self.request.get("key"))

        # Try to load the class.
        try:
            strategyClass = cls.Class(strategyClassName)
        except Exception, e:
            templateValues["error"] = "Failed to load strategy '%s': %s" % (strategyClassName, e)
            path = os.path.join(os.path.dirname(__file__), "..", "templates", 'error.html')
            self.response.out.write(template.render(path, templateValues))
            return

        # Get __init__ parameters.
        try:
            strategyParams = strategyClass.getMethodParams("__init__")
            minParamCount = 3
            if len(strategyParams) < minParamCount:
                raise Exception("__init__ should receive at least %d parameters. For example: __init__(self, feed, ...)" % minParamCount)
            strategyParams = strategyParams[minParamCount-1:]
        except Exception, e:
            templateValues["error"] = "Failed to get __init__ parameters for '%s': %s" % (strategyClassName, e)
            path = os.path.join(os.path.dirname(__file__), "..", "templates", 'error.html')
            self.response.out.write(template.render(path, templateValues))
            return

        form = QueueStrategyExecutionForm(self.request, strategyParams)

        # If handling a POST request, try to queue the new strategy execution.
        if isPost:
            try:
                form.validateAllParams()
                # Check that we have bars loaded for the given instrument within the given dates.
                instrument = form.getInstrument()
                beginDate = form.getParamAsDateTime(QueueStrategyExecutionForm.beginDateParam)
                endDate = form.getParamAsDateTime(QueueStrategyExecutionForm.endDateParam)
                if not persistence.Bar.hasBars(instrument, persistence.Bar.Type.DAILY, beginDate, endDate):
                    raise Exception("There are no bars loaded for '%s' between '%s' and '%s'" % (instrument, beginDate, endDate))

                # Queue the strategy execution config and redirect.
                stratExecConfig = self.__buildStratExecConfig(strategyClassName, strategyParams, form)
                stratExecConfig.put()
                usertasks.MasterTask(1, stratExecConfig).queue()
                self.redirect(StrategyPage.getUrl(strategyClassName))
            except Exception, e:
                templateValues["submit_error"] = str(e)
        # If this is a re-execution request, load form values from strat exec config.
        elif stratExecConfigKey != "":
            try:
                stratExecConfig = persistence.StratExecConfig.getByKey(stratExecConfigKey)
                form.loadFromStratExecConfig(stratExecConfig)
            except Exception, e:
                templateValues["error"] = "Failed to load previous execution: %s" % (e)
                path = os.path.join(os.path.dirname(__file__), "..", "templates", 'error.html')
                self.response.out.write(template.render(path, templateValues))
                return

        # Template values
        strategyValues = {}
        strategyValues["class"] = strategyClassName

        templateValues["logout_url"] = users.create_logout_url("/")
        templateValues["user"] = users.get_current_user()
        templateValues["strategy"] = strategyValues
        templateValues["form"] = form.getTemplateValues()

        # Build the response using the template.
        path = os.path.join(os.path.dirname(__file__), "..", "templates", 'queue_execution.html')
        self.response.out.write(template.render(path, templateValues))

    def get(self):
        return self.__handleRequest(False)

    def post(self):
        return self.__handleRequest(True)


def main():
    application = webapp.WSGIApplication([
        (StrategyPage.url, StrategyPage),
        (StrategyExecutionPage.url, StrategyExecutionPage),
        ], debug=True)

    run_wsgi_app(application)


if __name__ == "__main__":
    main()
