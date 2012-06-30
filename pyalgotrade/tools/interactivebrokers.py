# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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
.. module:: interactivebrokers
 :synopsis: Historical data downloader from Interactive Broker's TWS. 

.. note:: This module is using the IbPy module to interface with the TWS.
          Please consult with the webpage for install instructions:
          http://code.google.com/p/ibpy/

.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""
import csv

from ib.ext.EWrapper import EWrapper
from ib.ext.EClientSocket import EClientSocket
from ib.ext.Contract import Contract


class IBHistoricalDataWrapper(EWrapper):
        """Historical Data Dumper Class which loads the historical data from Intercative Brokers TWS. 
        The ticks are stored in a list. Each list element is a dict with the following keys:

        * reqId:       The ticker Id of the request to which this bar is responding. (int)
        * Date:        The date-time stamp of the start of the bar. The format is determined by the reqHistoricalData() formatDate parameter. (str)
        * Open:        The bar opening price. (float)
        * High:        The high price during the time covered by the bar. (float)
        * Low:         The low price during the time covered by the bar. (float)
        * Close:       The bar closing price. (float)
        * Volume:      The volume during the time covered by the bar. (int)
        * TradeCount:  When TRADES historical data is returned, represents the number of trades that occurred during the time period the bar covers (int)
        * WAP:         The weighted average price during the time covered by the bar. (float)
        * HasGaps:     Whether or not there are gaps in the data. (bool)
        """
        def __init__(self):
                EWrapper.__init__(self)

                # List of returned ticks
                self.__ticks = []

                # Tuple for error code and parameters
                self.__e = None

                # Status indicator
                self.__finished = False

        def historicalData(self, reqId, date, open, high, low, close, volume, count, WAP, hasGaps):
                """Stores the historical data from the IB Client Connection to the local tick list"""

                # EOD is signalled in the date variable, eg.:
                # date='finished-20120628  00:00:00-20120630  00:00:00'
                if date.find("finished") != -1:
                        self.__finished = True
                        return

                tick = {}
                tick['reqId'] = reqId
                tick['Date'] = date
                tick['Open'] = open
                tick['High'] = high
                tick['Low'] = low
                tick['Close'] = close
                tick['Volume'] = volume
                tick['TradeCount'] = count
                tick['WAP'] = WAP
                tick['HasGaps'] = hasGaps

                self.__ticks.append(tick)
        
        # Need to define these functions as they are called during TWS connection
        def managedAccounts(self, accountsList): pass
        def nextValidId(self, orderId): pass

        def error(self, e, param1=None, param2=None):
                """Error handler function for the IB Connection."""
                self.__e = (e, param1, param2)

                if e != -1:
                        print "ERROR: ", self.__e

        def connectionClosed(self):
                """Connection closed handler for the IB Connection."""
                self.__finished = True

        def waitForFinish(self):
                """Waits until the datastream processing is finished"""
                while not self.__finished or (self.__e != None and self.__e[0] != -1): 
                    pass

        def getTicks(self):
                """Return the list of tick tuples. Each list element is a dict, see the keys in the class documentation."""
                return self.__ticks

        def getError(self):
                """Returns the error tuple: (errorCode,param1,param2)"""
                return self.__e


# The Id for the request. Must be a unique value. When the data is received, it will be identified by this Id. 
# This is also used when canceling the historical data request.
# The Id is used and maintained by the each get_historical_data() function
__tickerId=0

def __ticks_to_csv(ticks):
        """Convert list of tick dictionary to list of CSV file rows
        Note: This function excludes the TWS Request ID from the data.
        """
        myCSV = []
        class _CSVDumper:
                @staticmethod
                def write(str):
                        myCSV.append(str)

        dw = csv.DictWriter(_CSVDumper, 
                            ['Date','Open','High','Low','Close','Volume','TradeCount','WAP','HasGaps'], 
                            extrasaction='ignore')
        dw.writeheader()
        dw.writerows(ticks)

        return myCSV

def get_historical_data(symbol, endTime, duration, barSize, 
                        secType='STK', exchange='SMART', currency='USD', 
                        whatToShow='TRADES', useRTH=0, formatDate=1, 
                        twsHost='localhost', twsPort=7496, twsClientID=0): 
        """Downloads historical data from IB through TWS.
        
        :param symbol: Ticker symbol
        :type symbol:  str
        :param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
        :type endTime:  str
        :param duration: This is the time span the request will cover, and is specified using the format: 
                         <integer> <unit>, i.e., 1 D, where valid units are:
                         S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
                         If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
        :type duration: str
        :param barSize: Specifies the size of the bars that will be returned (within IB/TWS limits). Valid values include:
                        1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
        :type barSize:  str
        :param whatToShow: Determines the nature of data being extracted. Valid values include:
                           TRADES, MIDPOINT, BID, ASK, BID_ASK, HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY
        :type whatToShow: str
        :param useRTH: Determines whether to return all data available during the requested time span, 
                       or only data that falls within regular trading hours. Valid values include:
                       0: All data is returned even where the market in question was outside of its regular trading hours.
                       1: Only data within the regular trading hours is returned, even if the requested time span
                       falls partially or completely outside of the RTH.
        :type useRTH: int
        :param formatDate: Determines the date format applied to returned bars. Valid values include:
                           1: Dates applying to bars returned in the format: yyyymmdd{space}{space}hh:mm:dd .
                           2: Dates are returned as a long integer specifying the number of seconds since 1/1/1970 GMT .
        :type formatDate: int
        :param twsHost: IP Address or Host where the TWS is running.
        :type twsHost: string
        :param twsPort: TCP Port where the TWS is listening.
        :type twsPort: int
        :param twsClientID: TWS Client ID. Must be unique for all connected clients.
        :type twsClientID: int
        """

        wrapper = IBHistoricalDataWrapper()
        connection = EClientSocket(wrapper)
        connection.eConnect(twsHost, twsPort, twsClientID)

        global __tickerId

        # This class contains attributes used to describe the contract.
        contract = Contract()
        contract.m_symbol   = symbol;
        contract.m_secType  = secType;
        contract.m_exchange = exchange;
        contract.m_currency = currency;

        connection.reqHistoricalData(__tickerId, contract, endTime, duration, barSize, whatToShow, useRTH, formatDate)
        wrapper.waitForFinish()
        connection.cancelHistoricalData(__tickerId)
        connection.eDisconnect()

        __tickerId += 1 # Increase __tickerId to have unique value in the next call

        error = wrapper.getError()
        if error[0] != -1:
                print "ERROR: ", error
                return

        ticks = wrapper.getTicks()

        return ticks


def get_1min_csv(symbol, endTime, duration): 
        """Downloads historical data from IB using 1 minute ticks

        :param symbol: Ticker symbol
        :type symbol: str
        :param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
        :type endTime:  str
        :param duration: This is the time span the request will cover, and is specified using the format: 
                         <integer> <unit>, i.e., 1 D, where valid units are:
                         S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
                         If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
        :type duration: str

        :rtype: List of the ticks, where each list element is a CSV row.
        """
        ticks = get_historical_data(symbol, endTime, duration, barSize='1 min')
        return __ticks_to_csv(ticks)

def get_5min_csv(symbol, endTime, duration):
        """Downloads historical data from IB using 5 minute ticks

        :param symbol: Ticker symbol
        :type symbol: str
        :param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
        :type endTime:  str
        :param duration: This is the time span the request will cover, and is specified using the format: 
                         <integer> <unit>, i.e., 1 D, where valid units are:
                         S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
                         If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
        :type duration: str

        :rtype: List of the ticks, where each list element is a CSV row.
        """
        ticks = get_historical_data(symbol, endTime, duration, barSize='5 mins')
        return __ticks_to_csv(ticks)

def get_daily_csv(symbol, endTime, duration): 
        """Downloads historical data from IB using 1 day ticks

        :param symbol: Ticker symbol
        :type symbol: str
        :param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.
        :type endTime:  str
        :param duration: This is the time span the request will cover, and is specified using the format: 
                         <integer> <unit>, i.e., 1 D, where valid units are:
                         S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
                         If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
        :type duration: str

        :rtype: List of the ticks, where each list element is a CSV row.
        """
        ticks = get_historical_data(symbol, endTime, duration, barSize='1 day')
        return __ticks_to_csv(ticks)


if __name__ == '__main__':
        import argparse

        parser = argparse.ArgumentParser(description='Historical data downloader from Interactive Broker\'s  TWS')
        parser.add_argument('--symbol',   help='Ticker symbol', required=True)
        parser.add_argument('--endtime',  help='Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a space at the end.',
                            nargs='*', required=True,
                           )
        parser.add_argument('--duration', help='This is the time span the request will cover, and is specified using the format:\n'
                                               '<integer> <unit>, i.e., 1 D, where valid units are:\n'
                                               'S (seconds),  D (days),  W (weeks),  M (months),  Y (years)\n'
                                               'If no unit is specified, seconds are used.',
                            default=['1', 'D'],
                            nargs=2,
                            )
        parser.add_argument('--barsize', help='Specifies the size of the bars that will be returned (within IB/TWS limits). Valid values include:\n'
                                              '1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day',
                            default=['5', 'mins'],
                            nargs=2,
                            )

        args = parser.parse_args()

        #symbol='SPY'
        #endTime='20120629 18:00 EST5EDT'
        #duration='1 D'
        #barSize='5 mins'
        ticks = get_historical_data(args.symbol, " ".join(args.endtime), " ".join(args.duration), " ".join(args.barsize))
        csv_rows = __ticks_to_csv(ticks)

        for row in csv_rows:
                print row, 
