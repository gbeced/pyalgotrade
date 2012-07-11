# PyAlgoTrade
# 
# Related materials
# Interactive Brokers API:  http://www.interactivebrokers.com/en/software/api/api.htm
# IbPy: http://code.google.com/p/ibpy/ 
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


"""
.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""

import logging, os, threading, copy, datetime
from time import localtime 

from pyalgotrade import observer

from ibbar import Bar

from ib.ext.EWrapper import EWrapper
from ib.ext.EClientSocket import EClientSocket
from ib.ext.ScannerSubscription import ScannerSubscription
from ib.ext.Contract import Contract
from ib.ext.Order import Order

LOGFMT='%(asctime)s [%(levelname)s] %(message)s'
logging.basicConfig(level=logging.DEBUG,
                    format=LOGFMT,
                    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyalgotrade.log'),
                    filemode='a+')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter(LOGFMT))
log = logging.getLogger("pyalgotrade.providers.interactivebrokers")
log.addHandler(console)

class Connection(EWrapper):
        '''Wrapper class for Interactive Brokers TWS Connection.

        This class exports the IB API's Order, Realtime- and Historical Market Data and Market Scanner features.

        The IB API architecture uses asynchronous callback based data model. The calls made synchronous where it makes
        sense (Order Execution, Historical Data & Market Scanner) and kept asynchronous with a subscription model for
        Realtime Data and Order Updates. 

        :param accountCode: Interactive Brokers Account Code. Shown in the right corner in TWS. Format: DUXXXXX
        :type accountCode: str
        :param timezone: the zone specifies the offset from coordinated universal time (utc, formerly referred to as 
                         "greenwich mean time")
        :type timezone: int
        :param twsHost: Hostname of the machine where the TWS is running. Default: localhost
        :type twsHost: str
        :param twsPort: Port number of the listening TWS. Default: 7496
        :type twsPort: int
        :param twsClientId: Client ID used for this TWS connection. Default: 27
        :type twsClientId: int
        '''

        def __init__(self, accountCode, timezone=0, twsHost='localhost', twsPort=7496, twsClientId=27):
                self.__accountCode = accountCode
                self.__zone = timezone

                # Errors returned by TWS, set by error()
                # Need to create this variable first as the client connection could
                # return error
                self.__error = {'tickerID': None, 'errorCode': None, 'errorString': None}

                log.info("Initiating TWS Connection (%s:%d, clientId=%d) with accountCode=%s" % 
                         (twsHost, twsPort, twsClientId, accountCode))

                # Connect to TWS and set self as EWrapper 
                self.__tws = EClientSocket(self)
                self.__tws.eConnect(twsHost, twsPort, twsClientId)


                # Unique Ticker ID stream for each TWS Request
                self.__tickerID = 0

                # Unique Order ID for each TWS Order
                # Initial value is set by nextValidId() callback
                self.__orderID = 0

                # Dictionary to map instruments to orderIDs
                self.__orderIDs = {}

                # Dictionary to map instruments to realtime bar tickerIDs
                self.__realtimeBarIDs = {}

                # Dictionary to map instruments to realtime bar observer events
                self.__realtimeBarEvents = {}
                
                # Dictionary to map instruments to historical data tickerIDs
                self.__historicalDataTickerIDs = {}

                # List to buffer historical data which is produced by 
                # historicalData(), consumed by requestHistoricalData()
                self.__historicalDataBuffer = []

                # Lock for the historicalDataBuffer
                self.__historicalDataLock = threading.Condition()

                # Dictionary to map instruments to tickerIDs for market scanner 
                self.__marketScannerIDs = {}
                
                # Lock for the historicalDataBuffer
                self.__marketScannerLock = threading.Condition()

                # List to buffer market scanner data between requestMarketScanner()
                # and scannerData 
                self.__marketScannerBuffer = []

                # Account and portfolio is represented by multidimensional maps
                # See updateAccountValue()/updatePortfolio() for valid keys
                self.__accountValues = {}
                self.__portfolio = {}

                # Conditional lock for account and portfolio updates
                self.__accUpdateLock = threading.Condition()
                self.__portfolioLock = threading.Condition()

                # Observer for Order Updates
                self.__orderUpdateHandler = observer.Event()

                # Subscribe for account updates
                self.__tws.reqAccountUpdates(True, accountCode)

        def __getNextTickerID(self):
                """Returns the next unique Ticker ID"""
                tickerID = copy.copy(self.__tickerID)
                self.__tickerID += 1
                return tickerID
        
        def __getNextOrderID(self):
                """Returns the next unique Order ID"""
                orderID = copy.copy(self.__orderID)
                self.__orderID += 1
                return orderID

        def getTimezone(self):
                """Returns the timezone. The zone specifies the offset from Coordinated Universal Time 
                (UTC, formerly referred to as "Greenwich Mean Time")
                """
                return self.__zone
        
        ########################################################################################
        # Requests for TWS
        ########################################################################################
        def createOrder(self, instrument, action, lmtPrice, auxPrice, orderType, totalQty, minQty,
                        tif, goodTillDate, trailingPct, trailStopPrice, transmit, whatif, 
                        secType='STK', exchange='SMART', currency='USD' ):
                """Creates a new order and sends it to the market via TWS
                
                :param instrument:
                :type instrument: str
                :param action: Identifies the side. Valid values are: BUY, SELL, SSHORT.
                :type action: str
                :param auxPrice: This is the STOP price for stop-limit orders, and the offset 
                                 amount for relative orders. In all other cases, specify zero.
                :type auxPrice: float
                :param lmtPrice: This is the LIMIT price, used for limit, stop-limit and relative orders. 
                                 In all other cases specify zero.
                :type lmtPrice: float
                :param orderType: Supported Order Types (this is just a subset of the IB's API, 
                                  for the full list check the API):
                                  STP, STP LMT, TRAIL LIT, TRAIL MIT, TRAIL, TRAIL LIMIT,
                                  MKT, LMT, LOC, LOO, LIT          
                :type orderType: str
                :param totalQty: The order quantity.
                :type totalQty: int
                :param minQty: Identifies a minimum quantity order type. 
                :type minQty: int
                :param tif: The time in force. Valid values are: DAY, GTC, IOC, GTD.
                :type tif: str
                :param goodTillDate: You must enter GTD as the time in force to use this string.
                                     The trade's "Good Till Date," format "YYYYMMDD hh:mm:ss (optional time zone)
                                     Use an empty String if not applicable.
                :type goodTillDate: str
                :param trailingPct: Specify the trailing amount of a trailing stop order as a percentage.
                                    Observe the following guidelines when using the trailingPercent field:
                                     - This field is mutually exclusive with the existing trailing amount. 
                                       That is, the API client can send one or the other but not both.
                                     - This field is read AFTER the stop price (barrier price) as follows: 
                                       deltaNeutralAuxPrice, stopPrice, trailingPercent, scale order attributes
                                     - The field will also be sent to the API in the openOrder message if the API 
                                       client version is >= 56. It is sent after the stopPrice field as follows:
                                       stopPrice, trailingPct, basisPoint
                :type trailingPct: float
                :param trailStopPrice: For TRAILLIMIT orders only
                :type trailStopPrice: float
                :param transmit: Specifies whether the order will be transmitted by TWS. If set to false, the order
                                 will be created at TWS but will not be sent.
                :type transmit: bool
                :param whatif: Use to request pre-trade commissions and margin information.
                               If set to true, margin and commissions data is received back via the OrderState()
                               object for the openOrder() callback.
                :type whatif: bool
                :param secType: This is the security type. Valid values are:
                                STK, OPT, FUT, IND, FOP, CASH, BAG
                :type secType: str
                :param exchange: The order destination, such as Smart.
                :type exchange: str
                :param currency: Specifies the currency for the trade.
                :type currency: str
                """
                orderID = self.__getNextOrderID()

                self.__orderIDs[orderID] = instrument
                
                contract = Contract()
                contract.m_symbol = instrument
                contract.m_secType = secType
                contract.m_exchange = exchange
                contract.m_currency = currency

                order = Order()
                order.m_action = action
                order.m_auxPrice = auxPrice
                order.m_lmtPrice = lmtPrice
                order.m_orderType = orderType
                order.m_totalQuantity = totalQty
                order.m_minQuantity = minQty
                order.m_goodTillDate = goodTillDate
                order.m_tif = tif
                order.m_trailingPct = trailingPct
                order.m_trailStopPrice = trailStopPrice
                order.m_transmit = transmit
                order.m_whatif = whatif

                self.__tws.placeOrder(orderID, contract, order)


        def cancelOrder(self, orderID):
                """Cancels an order.
                
                :param orderID: Order ID.
                :type orderID: str
                """
                self.__tws.cancelOrder(orderID)

        def subscribeOrderUpdates(self, handler):
                """Subscribes the handler for Order Updates from TWS.

                :param handler: Function which will be called on order state changes.
                :type handler: Function
                """
                self.__orderUpdateHandler.subscribe(handler)

        def subscribeRealtimeBars(self, instrument, handler, 
                                  secType='STK', exchange='SMART', currency='USD', 
                                  barSize=5, whatToShow='TRADES', useRTH=1):
                """Subscribes handler for realtime market data of instrument.

                :param instrument: Instrument's symbol
                :type instrument: str
                :param handler: The function which will be called on new market data (every 5 secs)
                :type handler: Function
                :param secType: This is the security type. Valid values are:
                                STK, OPT, FUT, IND, FOP, CASH, BAG
                :type secType: str
                :param exchange: The order destination, such as Smart.
                :type exchange: str
                :param currency: Specifies the currency for the trade.
                :type currency: str
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
                """
                if instrument not in self.__realtimeBarIDs:
                        # Register the tickerID with the instrument name
                        tickerID = self.__getNextTickerID()
                        self.__realtimeBarIDs[instrument] = tickerID

                        # Prepare the contract 
                        contract = Contract()
                        contract.m_symbol = instrument
                        contract.m_secType = secType
                        contract.m_exchange = exchange
                        contract.m_currency = currency
                        
                        # Request realtime data from TWS
                        self.__tws.reqRealTimeBars(tickerID, contract, barSize, whatToShow, useRTH)

                        # Register handler for the realtime bar event observer
                        self.__realtimeBarEvents[instrument] = observer.Event()
                        self.__realtimeBarEvents[instrument].subscribe(handler)

                else:
                        # Instrument already subscribed, add handler to the event observer
                        self.__realtimeBarEvents[instrument].subscribe(handler)

        def unsubscribeRealtimeBars(self, instrument, handler):
                """Cancels realtime data feed for the given instrument and handler.
                
                :param instrument: Instrument's symbol
                :type instrument: str
                :param handler: The function which will be called on new market data (every 5 secs)
                :type handler: Function
                """
                if instrument in self.__realtimeBarIDs:
                        tickerID = self.__realtimeBarIDs[instrument]

                        # TODO: Check for other observes and 
                        # deregister only if last is freed
                        self.__tws.cancelRealTimeBars(tickerID)

                        del self.__realtimeBarIDs[instrument]
                        del self.__realtimeBarEvents[instrument]
                        del self.__realtimeBarBuffer[instrument]
                else:
                        # Instrument was not subscribed, ignore
                        pass

        def requestHistoricalData(self, instrument, endTime, duration, barSize,
                                  secType='STK', exchange='SMART', currency='USD',
                                  whatToShow='TRADES', useRTH=0, formatDate=1):
                """Requests historical data. The historical bars are returned as a list of IBBar instances.
                
                :param instrument: Instrument's symbol
                :type instrument: str
                :param endTime: Use the format yyyymmdd hh:mm:ss tmz, where the time zone is allowed (optionally) after a 
                                space at the end.
                :type endTime:  str
                :param duration: This is the time span the request will cover, and is specified using the format: 
                                 <integer> <unit>, i.e., 1 D, where valid units are:
                                 S (seconds),  D (days),  W (weeks),  M (months),  Y (years)
                                 If no unit is specified, seconds are used.  Also, note "years" is currently limited to one.
                :type duration: str
                :param barSize: Specifies the size of the bars that will be returned (within IB/TWS limits). Valid values include:
                                1 sec, 5 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 15 mins, 30 mins, 1 hour, 1 day
                :type barSize:  str
                :param secType: This is the security type. Valid values are:
                                STK, OPT, FUT, IND, FOP, CASH, BAG
                :type secType: str
                :param exchange: The order destination, such as Smart.
                :type exchange: str
                :param currency: Specifies the currency for the trade.
                :type currency: str
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
                """
                # Get a unique tickerID for the request
                tickerID = self.__getNextTickerID()

                # Prepare the Contract for the historical data order
                contract = Contract()
                contract.m_symbol   = instrument;
                contract.m_secType  = secType;
                contract.m_exchange = exchange;
                contract.m_currency = currency;

                # map the tickerID to instrument
                self.__historicalDataTickerIDs[tickerID] = instrument

                # Request historical data
                self.__tws.reqHistoricalData(tickerID, contract, endTime, duration, barSize, whatToShow, useRTH, formatDate)

                # Wait for the result to appear in the buffer
                self.__historicalDataLock.acquire()
                self.__historicalDataLock.wait()
                self.__historicalDataLock.release()

                # Copy the downloaded historical data and empty the buffer
                historicalData = copy.copy(self.__historicalDataBuffer)
                self.__historicalDataBuffer = []

                return historicalData 
                

        def requestMarketScanner(self, numberOfRows=10, 
                                 scanCode='TOP_PERC_GAIN', abovePrice=0,
                                 locationCode='STK.US.MAJOR', instrument='STK'):
                tickerID = self.__getNextTickerID()

                subscript = ScannerSubscription()
                subscript.numberOfRows(numberOfRows)
                subscript.locationCode(locationCode)
                # subscript.abovePrice(abovePrice)
                subscript.scanCode(scanCode)
                subscript.instrument(instrument)

                self.__tws.reqScannerSubscription(tickerID, subscript)
                
                self.__marketScannerLock.acquire()
                self.__marketScannerLock.wait()
                self.__marketScannerLock.release()

                marketScannerData = copy.copy(self.__marketScannerBuffer)
                self.__marketScannerBuffer = []

                return marketScannerData

        def requestAccountUpdate(self):
                self.__tws.reqAccountUpdates(True, self.__accountCode)

        def getCash(self, currency='USD'):
                self.__accUpdateLock.acquire()
                
                # Try to load cash
                cash = None
                cashReturned = False
                while not cashReturned:
                    try:
                        cash = float(self.__accountValues[self.__accountCode][currency]['TotalCashBalance'])
                    except KeyError:
                        self.__accUpdateLock.wait()
                    else:
                        cashReturned = True

                self.__accUpdateLock.release()

                return(cash)

        def getAccountValues(self):
                return self.__accountValues

        def getPortfolio(self):
                return self.__portfolio

        ########################################################################################
        # EWrapper callbacks
        ########################################################################################
        def historicalData(self, tickerID, date, open_, high, low, close, volume, tradeCount, vwap, hasGaps):
                instrument = self.__historicalDataTickerIDs[tickerID]

                # EOD is signaled in the date variable, eg.:
                # date='finished-20120628  00:00:00-20120630  00:00:00'
                if date.find("finished") != -1:
                    # Signal the requestHistoricalData 
                    self.__historicalDataLock.acquire()
                    self.__historicalDataLock.notify()
                    self.__historicalDataLock.release()
                    
                    return
                        
                # Convert the time to local time
		dt = datetime.datetime.strptime(date, "%Y%m%d  %H:%M:%S")
		dt += datetime.timedelta(hours= (-1 * self.__zone))

                # Create the bar
                bar = Bar(instrument, dt,
                          open_, high, low, close,
                          volume, vwap, tradeCount)

                # Append it to the buffer
                self.__historicalDataBuffer.append(bar)

        def realtimeBar(self, tickerID, time_, open_, high, low, close, volume, vwap, tradeCount):
                """
                This function receives the real-time bars data results and sends them to subscribers
                of __realtimeBarEvents.

                :param tickerID: The ticker Id of the request to which this bar is responding.
                :type tickerID: int
                :param time_: The date-time stamp of the start of the bar. The format is 
                              determined by the reqHistoricalData() formatDate parameter.
                :type time_: str
                :param open_: The bar opening price.
                :type open_: float
                :param high: The high price during the time covered by the bar.
                :type high: float
                :param low: The low price during the time covered by the bar.
                :type low: float
                :param close: The bar closing price.
                :type close: float
                :param volume: The volume during the time covered by the bar.
                :type volume: int
                :param vwap: The weighted average price during the time covered by the bar.
                :type vwap: float
                :param tradeCount: When TRADES historical data is returned, represents 
                                   the number of trades that occurred during the time 
                                   period the bar covers.
                :type tradeCount: int

                """
                # Convert the timezone to the destination timezone
                lt = localtime(time_)
                dt = datetime.datetime(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
		dt += datetime.timedelta(hours= (-1 * self.__zone))

                # Look up the instrument's name based on its tickerID
                for i in self.__realtimeBarIDs:
                    if self.__realtimeBarIDs[i] == tickerID:
                        instrument = i

                log.debug("RT Bar: %s [%d] time=%s open=%.2f high=%.2f low=%.2f close=%.2f volume=%d wap=%.2f tradeCount=%d" % 
                          (instrument, tickerID, dt, open_, high, low, close, volume, vwap, tradeCount))

                self.__realtimeBarEvents[instrument].emit(Bar(instrument, dt,
                                                              open_, high, low, close,
                                                              volume, vwap, tradeCount))

        
        def scannerData(self, tickerID, rank, contractDetails, distance, benchmark, projection, legsStr):
                """
                This function receives the requested market scanner data results and appends it to the
                market scanner buffer.

                :param tickerID: The ticker ID of the request to which this row is responding.
                :type tickerID: int
                :param rank: The ranking within the response of this bar.
                :type rank: int
                :param contractDetails: This object contains a full description of the contract.
                :type contractDetails: :class:`ib.ext.ContractDetails` (IbPy)
                :param distance: Varies based on query.
                :type distance: str
                :param benchmark: Varies based on query.
                :type benchmark: str
                :param projection: Varies based on query.
                :type projection: str
                :param legsStr: Describes combo legs when scan is returning EFP.
                :type legsStr: str
                """

                self.__marketScannerBuffer.append((tickerID, rank, contractDetails.m_summary.m_symbol, distance, benchmark, 
                                                   projection, legsStr))

        def scannerDataEnd(self, tickerID):
                """This function is called when the snapshot is received and marks the end of one scan.
                This function will notify the requestMarketScanner() function that data is available in the buffer.

                :param tickerID: The ticker ID of the request to which this row is responding.
                :type tickerID: int
                """
                self.__marketScannerLock.acquire()
                self.__marketScannerLock.notify()
                self.__marketScannerLock.release()

        def updateAccountValue(self, key, value, currency, accountName):
                """
                This function is called only when ReqAccountUpdates has been called.
                It will notify the __accUpdateLock waiters (e.g. getCash()) if new data is available.

                :param key: A string that indicates one type of account value.
                :type key:  str
                            Valid keys:
                            CashBalance             - Account cash balance
                            Currency                - Currency string
                            DayTradesRemaining      - Number of day trades left
                            EquityWithLoanValue     - Equity with Loan Value
                            InitMarginReq           - Current initial margin requirement
                            LongOptionValue         - Long option value
                            MaintMarginReq          - Current maintenance margin
                            NetLiquidation          - Net liquidation value
                            OptionMarketValue       - Option market value
                            ShortOptionValue        - Short option value
                            StockMarketValue        - Stock market value
                            UnalteredInitMarginReq  - Overnight initial margin requirement
                            UnalteredMaintMarginReq - Overnight maintenance margin requirement
                :param value: The value associated with the key.
                :type value: str
                :param currency: Defines the currency type, in case the value is a currency type.
                :type currency: str
                :param account: States the account to which the message applies.
                :type account: str

                """
                self.__accUpdateLock.acquire()

                # log.debug('updateAccountValue key=%s, value=%s, currency=%s, accountCode=%s' % (key, value, currency, accountName))
                self.__accountValues.setdefault(accountName, {})
                self.__accountValues[accountName].setdefault(currency, {})
                self.__accountValues[accountName][currency].setdefault(key, {})

                self.__accountValues[accountName][currency][key] = value

                self.__accUpdateLock.notify()
                self.__accUpdateLock.release()

        def updatePortfolio(self, contract, position, marketPrice, marketValue, 
                            avgCost, unrealizedPNL, realizedPNL, accountName):
                """
                This function is called only when ReqAccountUpdates has been called.
                It will notify the __portfolioLock waiters if new data is available.
                
                :param contract: This structure contains a description of the contract which 
                                 is being traded. The exchange field in a contract is not set 
                                 for portfolio update.
                :type contract: Contract
                :param position: This integer indicates the position on the contract. 
                                 If the position is 0, it means the position has just cleared.
                :type position: int
                :param marketPrice: Unit price of the instrument.
                :type marketPrice: float
                :param marketValue: The total market value of the instrument.
                :type marketValue: float
                :param avgCost: The average cost per share is calculated by dividing your cost 
                                (execution price + commission) by the quantity of your position.
                :type avgCost: float
                :param unrealizedPNL: The difference between the current market value of your 
                                      open positions and the average cost, 
                                      or Value - Average Cost.
                :type unrealizedPNL: float
                :param realizedPNL: Shows your profit on closed positions, which is the 
                                    difference between your entry execution cost 
                                    (execution price + commissions to open the position) and 
                                    exit execution cost (execution price + commissions to 
                                    close the position)
                :type realizedPNL: float
                :param accountName: States the account to which the message applies. 
                :type accountName: str

                """
                log.debug("accountCode=%s, contract=%s, position=%d, marketPrice=%.2f, marketValue=%.2f, avgCost=%.2f, unrealizedPNL=%.2f, realizedPNL=%.2f" % (accountName, contract.m_symbol, position, marketPrice, marketValue, avgCost, unrealizedPNL, realizedPNL))
                instrument = contract.m_symbol

                self.__portfolioLock.acquire()

                self.__portfolio.setdefault(accountName, {})
                self.__portfolio[accountName].setdefault(instrument, {})

                self.__portfolio[accountName][instrument][contract] = contract
                self.__portfolio[accountName][instrument][position] = position
                self.__portfolio[accountName][instrument][marketPrice] = marketPrice
                self.__portfolio[accountName][instrument][marketValue] = marketValue
                self.__portfolio[accountName][instrument][avgCost] = avgCost
                self.__portfolio[accountName][instrument][unrealizedPNL] = unrealizedPNL
                self.__portfolio[accountName][instrument][realizedPNL] = realizedPNL
                
                self.__portfolioLock.notify()
                self.__portfolioLock.release()

        def updateAccountTime(self, timestamp): 
                """This function is called only when reqAccountUpdates on EClientSocket object has been called.
                Logs the account update time.

                :param timestamp: This indicates the last update time of the account information
                :type timestamp: str
                """
                log.info("Last account update time: %s", timestamp)

        def orderStatus(self, orderID, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld):
                """This event is called whenever the status of an order changes. It is also fired after 
                reconnecting to TWS if the client has any open orders.

                Note:  It is possible that orderStatus() may return duplicate messages. It is essential 
                that you filter the message accordingly.

                :param orderID: The order ID that was specified previously in the call to placeOrder()
                :type orderID: int
                :param status: The order status. Possible values include:
                               PendingSubmit, PendingCancel, PreSubmitted, Submitted, Cancelled, Filled, Inactive
                :type status: str
                :param filled: Specifies the number of shares that have been executed.
                :type filled: int
                :param remaining: Specifies the number of shares still outstanding.
                :type remaining: int 
                :param avgFillPrice: The average price of the shares that have been executed. This parameter 
                                      is valid only if the filled parameter value is greater than zero. 
                                      Otherwise, the price parameter will be zero.
                :type avgFillPrice: float
                :param permId: The TWS id used to identify orders. Remains the same over TWS sessions.
                :type permId: int
                :param parentId: The order ID of the parent order, used for bracket and auto trailing stop orders.
                :type parentId: int
                :param lastFillPrice: The last price of the shares that have been executed. 
                                      This parameter is valid only if the filled parameter value is greater than zero. 
                                      Otherwise, the price parameter will be zero.
                :type lastFillPrice: float
                :param clientId: The ID of the client (or TWS) that placed the order. Note that TWS orders have a fixed 
                                 clientId and orderId of 0 that distinguishes them from API orders.
                :type clientId: int
                :param whyHeld: This field is used to identify an order held when TWS is trying to locate shares for a short sell. 
                                The value used to indicate this is 'locate'.
                :type whyHeld: str
                """
                log.info("Order status: orderID: %s, status: %s, filled: %d, remaining: %d, avgFillPrice: %.2f, permId: %s, "
                         "parentId:%s, lastFillPrice: %.2f, clientId:%d, whyHeld: %s" % 
                         (orderID, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,  whyHeld))
                try:
                    instrument = self.__orderIDs[orderID]
                except KeyError:
                    instrument = "UNKNOWN"

                self.__orderUpdateHandler.emit(orderID, instrument, status, filled, remaining, avgFillPrice, lastFillPrice)

        def openOrder(self, orderID, contract, order, orderState):
                log.info("openOrder: orderID: %s, instrument: %s", orderID, contract.m_symbol)
                self.__orderIDs[orderID] = contract.m_symbol

        def managedAccounts(self, accountsList): 
                """Logs the managed account list by this TWS connection."""
                log.info("Managed account list: %s", accountsList)
        
        def nextValidId(self, orderID): 
                """This function is called after a successful connection to TWS.

                The next available order ID received from TWS upon connection. 
                Increment all successive orders by one based on this ID.
                """
                self.__orderID = orderID

                log.info("First valid orderID: %d", orderID)

        def error(self, tickerID, errorCode=None, errorString=None):
                """Error handler function for the IB Connection."""
                self.__error['tickerID'] = tickerID
                self.__error['errorCode'] = errorCode
                self.__error['errorString'] = errorString

                if 0 <= errorCode < 1000:
                        # Errors
                        log.error( '%s, %s, %s' %(tickerID, errorCode, errorString))
                elif 1000 <= errorCode < 2000:
                        # System messages
                        log.info( 'System message: %s, %s, %s' %(tickerID, errorCode, errorString))
                elif 2000 <= errorCode < 3000:
                        # Warning messages
                        log.warn( '%s, %s, %s' %(tickerID, errorCode, errorString))

                if tickerID != -1:
                        log.error( 'error: %s, %s, %s' %(tickerID, errorCode, errorString))

        def winError(self, errorMsg, errorCode): 
                """Error handler function for the TWS Client side errors."""
                log.error("WINERROR: %d: %s", errorCode, errorMsg)

        def connectionClosed(self):
                """Connection closed handler for the IB Connection."""
                log.error("Connection closed")
