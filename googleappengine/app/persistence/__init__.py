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

from google.appengine.ext import db

import hashlib


######################################################################
## Internal helper functions

def get_md5(value):
    m = hashlib.md5()
    m.update(value)
    return m.hexdigest()


class StratExecConfig(db.Model):
    class Status:
        ACTIVE = 1
        FINISHED = 2
        CANCELED_TOO_MANY_ERRORS = 3

    className = db.StringProperty(required=True)
    instrument = db.StringProperty(required=True)
    barType = db.IntegerProperty(required=True)
    firstDate = db.DateTimeProperty(required=True)
    lastDate = db.DateTimeProperty(required=True)
    parameterNames = db.StringListProperty(required=True)
    parameterRanges = db.ListProperty(item_type=int, required=True)  # 2 values for each parameter (first, last)
    created = db.DateTimeProperty(required=True)
    status = db.IntegerProperty(required=True)

    # Execution info.
    errors = db.IntegerProperty(default=0)  # Number of errors hit.
    totalExecutions = db.IntegerProperty(required=True)
    executionsFinished = db.IntegerProperty(default=0)
    bestResult = db.FloatProperty(required=False, default=0.0)
    bestResultParameters = db.ListProperty(item_type=int, default=None)

    @staticmethod
    def getByKey(key):
        return db.get(key)

    @staticmethod
    def getByClass(className, statusList):
        query = db.GqlQuery("select *"
                            " from StratExecConfig"
                            " where className = :1"
                            " and status in :2"
                            " order by created desc",
                            className, statusList)
        return query.run()

    @staticmethod
    def getByStatus(statusList):
        query = db.GqlQuery("select * from StratExecConfig"
                            " where status in :1"
                            " order by created desc",
                            statusList)
        return query.run()


class Bar(db.Model):
    class Type:
        DAILY = 1

    instrument = db.StringProperty(required=True)
    barType = db.IntegerProperty(required=True)
    dateTime = db.DateTimeProperty(required=True)
    open_ = db.FloatProperty(required=True)
    close_ = db.FloatProperty(required=True)
    high = db.FloatProperty(required=True)
    low = db.FloatProperty(required=True)
    volume = db.FloatProperty(required=True)
    adjClose = db.FloatProperty(required=True)

    @staticmethod
    def getKeyName(instrument, barType, dateTime):
        return get_md5("%s %s %s" % (instrument, str(barType), str(dateTime)))

    @staticmethod
    def getOrCreate(instrument, barType, dateTime, open_, close_, high, low, volume, adjClose):
        instrument = instrument.upper()
        keyName = Bar.getKeyName(instrument, barType, dateTime)
        return Bar.get_or_insert(key_name=keyName, barType=barType, instrument=instrument, dateTime=dateTime, open_=open_, close_=close_, high=high, low=low, volume=volume, adjClose=adjClose)

    @staticmethod
    def getBars(instrument, barType, fromDateTime, toDateTime):
        instrument = instrument.upper()
        query = db.GqlQuery("select *"
                            " from Bar"
                            " where instrument = :1"
                            " and barType = :2"
                            " and dateTime >= :3"
                            " and dateTime <= :4",
                            instrument, barType, fromDateTime, toDateTime)
        return query.run()

    @staticmethod
    def hasBars(instrument, barType, fromDateTime, toDateTime):
        instrument = instrument.upper()
        query = db.GqlQuery("select *"
                            " from Bar"
                            " where instrument = :1"
                            " and barType = :2"
                            " and dateTime >= :3"
                            " and dateTime <= :4"
                            " limit 1",
                            instrument, barType, fromDateTime, toDateTime)
        return query.get() is not None
