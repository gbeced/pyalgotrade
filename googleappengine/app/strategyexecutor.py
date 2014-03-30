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

from google.appengine.api import memcache

from common import logger
from common import cls
import persistence
from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade.barfeed import membf

import pickle
import zlib


class MemBarFeed(membf.BarFeed):
    def barsHaveAdjClose(self):
        return True


# Converts a persistence.Bar to a pyalgotrade.bar.Bar.
def ds_bar_to_pyalgotrade_bar(dsBar):
    return bar.BasicBar(dsBar.dateTime, dsBar.open_, dsBar.high, dsBar.low, dsBar.close_, dsBar.volume, dsBar.adjClose, bar.Frequency.DAY)


# Loads pyalgotrade.bar.Bars objects from the db.
def load_pyalgotrade_daily_bars(instrument, barType, fromDateTime, toDateTime):
    assert(barType == persistence.Bar.Type.DAILY)
    # Load pyalgotrade.bar.Bar objects from the db.
    dbBars = persistence.Bar.getBars(instrument, barType, fromDateTime, toDateTime)
    bars = [ds_bar_to_pyalgotrade_bar(dbBar) for dbBar in dbBars]

    # Use a feed to build pyalgotrade.bar.Bars objects.
    feed = MemBarFeed(bar.Frequency.DAY)
    feed.addBarsFromSequence(instrument, bars)
    ret = []
    for dateTime, bars in feed:
        ret.append(bars)
    return ret


class BarsCache:
    def __init__(self, aLogger):
        self.__cache = {}
        self.__logger = aLogger

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
            if value is not None:
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
        if ret is None:
            ret = self.__getFromMemCache(key)
            if ret is not None:
                # Store in local cache for later use.
                self.__addLocal(key, ret)
        return ret


class StrategyExecutor:
    def __init__(self):
        self.__logger = logger.Logger(20)
        self.__barCache = BarsCache(self.__logger)

    def __loadBars(self, stratExecConfig):
        ret = self.__barCache.get(stratExecConfig.key())
        if ret is None:
            self.__logger.info("Loading '%s' bars from %s to %s" % (stratExecConfig.instrument, stratExecConfig.firstDate, stratExecConfig.lastDate))
            ret = load_pyalgotrade_daily_bars(stratExecConfig.instrument, stratExecConfig.barType, stratExecConfig.firstDate, stratExecConfig.lastDate)
            self.__barCache.add(stratExecConfig.key(), ret)
            self.__logger.info("Finished loading '%s' bars from %s to %s" % (stratExecConfig.instrument, stratExecConfig.firstDate, stratExecConfig.lastDate))
        return ret

    def getLogger(self):
        return self.__logger

    def runStrategy(self, stratExecConfig, paramValues):
        bars = self.__loadBars(stratExecConfig)

        barFeed = barfeed.OptimizerBarFeed(bar.Frequency.DAY, [stratExecConfig.instrument], bars)

        # Evaluate the strategy with the feed bars.
        params = [barFeed]
        params.extend(paramValues)
        myStrategy = cls.Class(stratExecConfig.className).getClass()(*params)
        myStrategy.run()
        return myStrategy.getResult()
