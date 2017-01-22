# MySQLFeed based on sqlitefeed from PyAlgoTrade
#
# Copyright 2016-2017 Richard Hagen
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

"""
.. moduleauthor:: Richard Hagen <richard.hagen@gmail.com>
"""

from pyalgotrade.barfeed import dbfeed
from pyalgotrade.barfeed import membf
from pyalgotrade import bar
from pyalgotrade.utils import dt
import pymysql


def normalize_instrument(instrument):
    return instrument.upper()


class Database(dbfeed.Database):
    def __init__(self, hostname, database, username, password, charset='utf8mb4'):
        self.__instrumentIds = {}
        self.__connection = pymysql.connect(host=hostname,
                             user=username,
                             password=password,
                             db=database,
                             charset=charset,
                             cursorclass=pymysql.cursors.DictCursor)

    def __findInstrumentId(self, instrument):
        cursor = self.__connection.cursor()
        sql = "select symbol_id from stock_data where symbol_id = %s group_by symbol_id"
        cursor.execute(sql, [instrument])
        ret = cursor.fetchone()
        if ret is not None:
            ret = ret['symbol_id']
        cursor.close()
        return ret

    def __getOrCreateInstrument(self, instrument):
        # Try to get the instrument id from the cache.
        ret = self.__instrumentIds.get(instrument, None)
        if ret is not None:
            return ret
        # If its not cached, get it from the db.
        ret = self.__findInstrumentId(instrument)
        # Cache the id.
        self.__instrumentIds[instrument] = ret
        return ret

    def createSchema(self):

        self.__connection.execute("CREATE TABLE `stock_data` ("
              "id bigint(20) NOT NULL AUTO_INCREMENT,"
              "symbol_id varchar(50) COLLATE utf8_unicode_ci NOT NULL,"
              "timestamp datetime NOT NULL,"
              "frequency int(11) NOT NULL,"
              "open double NOT NULL,"
              "high double NOT NULL,"
              "low double NOT NULL,"
              "close double NOT NULL,"
              "volume double NOT NULL,"
              "adjusted_close double NOT NULL,"
              "PRIMARY KEY (`id`),"
              "KEY dx_stock_data_symbol_id (symbol_id),"
              "KEY idx_stock_data_timestamp (timestamp)"
            ") ENGINE=InnoDB AUTO_INCREMENT=28119607 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;")

    def addBar(self, instrument, bar, frequency):
        instrument = normalize_instrument(instrument)
        instrumentId = self.__getOrCreateInstrument(instrument)
        timeStamp = dt.datetime_to_timestamp(bar.getDateTime())

        try:
            sql = "insert into bar (symbol_id, frequency, timestamp, open, high, low, close, volume, adjusted_close)" \
                    "values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            params = [instrumentId, frequency, timeStamp, bar.getOpen(), bar.getHigh(), bar.getLow(), bar.getClose(), bar.getVolume(), bar.getAdjClose()]
            self.__connection.execute(sql, params)
        except pymysql.IntegrityError:
            sql = "update bar set open = %s, high = %s, low = %s, close = %s, volume = %s, adjusted_close = %s" \
                " where symbol_id = %s and frequency = %s and timestamp = %s"
            params = [bar.getOpen(), bar.getHigh(), bar.getLow(), bar.getClose(), bar.getVolume(), bar.getAdjClose(), instrumentId, frequency, timeStamp]
            self.__connection.execute(sql, params)

    def getBars(self, instrument, frequency, timezone=None, fromDateTime=None, toDateTime=None):
        instrument = normalize_instrument(instrument)
        sql = "select timestamp, open, high, low, close, volume, adjusted_close, frequency from stock_data" \
              " where symbol_id = %s and frequency = %s "
        args = [instrument, frequency]

        if fromDateTime is not None:
            sql += " and timestamp >= %s"
            args.append(fromDateTime)
        if toDateTime is not None:
            sql += " and timestamp <= %s"
            args.append(toDateTime)

        sql += " order by timestamp asc"
        cursor = self.__connection.cursor()
        cursor.execute(sql, args)

        result = cursor.fetchall()
        ret = [bar.BasicBar(row['timestamp'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume'],
                row['adjusted_close'],
                row['frequency']) for row in result]

        cursor.close()
        return ret

    def disconnect(self):
        self.__connection.close()
        self.__connection = None

class Feed(membf.BarFeed):
    def __init__(self, frequency, maxLen=None):
        super(Feed, self).__init__(frequency, maxLen)

        self.__db = Database("localhost","richard_stocks", "root", "abcd1234")

    def barsHaveAdjClose(self):
        return True

    def getDatabase(self):
        return self.__db

    def loadBars(self, instrument, timezone=None, fromDateTime=None, toDateTime=None):
        bars = self.__db.getBars(instrument, self.getFrequency(), timezone, fromDateTime, toDateTime)
        self.addBarsFromSequence(instrument, bars)
