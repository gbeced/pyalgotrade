"""
Interactive brokers live feed module

Requires:
- ibPy - https://github.com/blampe/IbPy
- trader work station or IB Gateway - https://www.interactivebrokers.com/en/?f=%2Fen%2Fsoftware%2Fibapi.php&ns=T

PyAlgoTrade
ib live broker

.. moduleauthor:: Kimble Young <kbcool@gmail.com>
"""

import time
import datetime
import threading
import Queue
import random
import sys
import pytz

from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade import dataseries
from pyalgotrade import resamplebase
import pyalgotrade.logger
from pyalgotrade.utils import dt
from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message



def utcnow():
    return dt.as_utc(datetime.datetime.utcnow())


def makeContract(contractTuple):
    newContract = Contract()
    newContract.m_symbol = contractTuple[0]
    newContract.m_secType = contractTuple[1]
    newContract.m_exchange = contractTuple[2]
    newContract.m_currency = contractTuple[3]
    newContract.m_expiry = contractTuple[4]
    newContract.m_strike = contractTuple[5]
    newContract.m_right = contractTuple[6]
    if len(contractTuple) > 7:
        if contractTuple[1] == "OPT":
            newContract.m_multiplier = contractTuple[7]
    return newContract

class BarEvent():
    ON_BARS = 1



class LiveFeed(barfeed.BaseBarFeed):
    """ real-time BarFeed that builds bars using IB API
    :param host: hostname of IB API (localhost)
    :param port: port the IB API listens on 
    :param identifiers: A list with the fully qualified identifier for the securities including the exchange suffix.
    :type identifiers: list.
    :param frequency: The frequency of the bars.
        Must be greater than or equal to **bar.Frequency.MINUTE** and less than or equal to **bar.Frequency.DAY**.


    :param maxLen: The maximum number of values that the :class:`pyalgotrade.dataseries.bards.BarDataSeries` will hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the opposite end.
    :type maxLen: int.
    :param marketOptions: What asset type, currency and routing method to use for Interactive Brokers. Eg assetType:'STK', currency:'USD', routing:'SMART'
    :type marketOptions: dictionary

    :param warmupBars: How many historical bars to start with
    type warmupBars: int

    :param debug: print all output of IB API calls
    :type debug: bool.

    """

    QUEUE_TIMEOUT = 0.01


    def __init__(self, identifiers, frequency, host="localhost",port=7496, maxLen=dataseries.DEFAULT_MAX_LEN,marketOptions={'assetType':'STK', 'currency':'GBP','routing': 'SMART'}, warmupBars = 0, debug=False):
        barfeed.BaseBarFeed.__init__(self, frequency, maxLen)
        if not isinstance(identifiers, list):
            raise Exception("identifiers must be a list")

              
        self.__frequency = frequency
        self.__timer = None

        '''
        valid frequencies are (and we are really limited by IB here but it's a good range). If the values don't suit then look at taking a higher frequency and using http://gbeced.github.io/pyalgotrade/docs/v0.16/html/strategy.html#pyalgotrade.strategy.BaseStrategy.resampleBarFeed to get the desired frequency
            - 1 minute - 60 - bar.Frequency.MINUTE 
            - 2 minutes - 120 - (bar.Frequency.MINUTE * 2)
            - 5 minutes - 300 - (bar.Frequency.MINUTE * 5)
            - 15 minutes - 900 - (bar.Frequency.MINUTE * 15)
            - 30 minutes - 1800 - (bar.Frequency.MINUTE * 30)
            - 1 hour - 3600 - bar.Frequency.HOUR
            - 1 day - 86400 - bar.Frequency.DAY

            Note: That instrument numbers and frequency affect pacing rules. Keep it to 3 instruments with a 1 minute bar to avoid pacing. Daily hits could include as many as 60 instruments as the limit is 60 calls within a ten minute period. We make one request per instrument for the warmup bars and then one per instrument every frequency seconds. See here for more info on pacing - https://www.interactivebrokers.com/en/software/api/apiguide/tables/historical_data_limitations.htm

        '''
        if self.__frequency not in [60,120,300,900,1800,3600,86400]:
            raise Exception("Please use a frequency of 1,2,5,15,30,60 minutes or 1 day")

        #builds up a list of quotes
        self.__queue = Queue.Queue()
        self.__currentBar = {}

        #keep track of latest timestamp on any bars for requesting next set
        self.__lastBarStamp = 0
        self.__currentBarStamp = 0
        self.__synchronised = False #have we synced to IB's bar pace yet?

        if debug == False:
            self.__debug = False
        else:
            self.__debug = True

        for instrument in identifiers:
            self.registerInstrument(instrument)

        self.__instruments = identifiers
        self.__contracts = []

        self.__ib = ibConnection(host=host,port=port,clientId=random.randint(1,10000))

        self.__ib.register(self.__historicalBarsHandler, message.historicalData)
        self.__ib.register(self.__errorHandler, message.error)
        self.__ib.register(self.__disconnectHandler, 'ConnectionClosed')

        self.__ib.registerAll(self.__debugHandler)

        self.__ib.connect()


        #IB market options

        self.__marketOptions = {}

        if marketOptions.get('assetType') == None:
            self.__marketOptions['assetType'] = 'STK'
        else:
            self.__marketOptions['assetType'] = marketOptions['assetType']

        if marketOptions.get('currency') == None:
            self.__marketOptions['currency'] = 'GBP'
        else:
            self.__marketOptions['currency'] = marketOptions['currency']

        if marketOptions.get('routing') == None:
            self.__marketOptions['routing'] = 'SMART'
        else:
            self.__marketOptions['routing'] = marketOptions['routing']

        #build contracts
        contractDict = {}
        for tickId in range(len(self.__instruments)):
            contractDict[tickId] = (self.__instruments[tickId], self.__marketOptions['assetType'], self.__marketOptions['routing'], self.__marketOptions['currency'], '', 0.0, '')
            stkContract = makeContract(contractDict[tickId])
            self.__contracts.append(stkContract)


        
        #warming up?
        self.__numWarmupBars = 0       #number of warmup bars to use
        self.__warmupBars = dict((el,[]) for el in self.__instruments)        #the warmup bars arrays indexed by stock code
        self.__inWarmup = False        #are we still in the warmup phase - when finished warming up this is set to false
        self.__stockFinishedWarmup = dict((el,False) for el in self.__instruments)  #has this stock finished warming up? create dict keyed by stock and set to false
        if warmupBars > 0:
            if warmupBars > 200:
                raise Exception("Max number of warmup bars is 200")

            self.__numWarmupBars = warmupBars
            self.__inWarmup = True
            self.__requestWarmupBars()
        else:
            #start the clock
            self.__requestBars()
        


    def __build_bar(self,barMsg, identifier,frequency):
        # "StartDate": "3/19/2014"
        # "StartTime": "9:55:00 AM"
        # "EndDate": "3/19/2014"
        # "EndTime": "10:00:00 AM"
        # "UTCOffset": 0
        # "Open": 31.71
        # "High": 31.71
        # "Low": 31.68
        # "Close": 31.69
        # "Volume": 2966
        # "Trades": 19
        # "TWAP": 31.6929
        # "VWAP": 31.693

        #Note date/time is local time not market time
        #Also for some weird reason IB is sending bars with finished in the date so why not just ignore

        ts = 0

        try:
            (offset, tz) = self.__marketCloseTime(self.__marketOptions['currency'])
            if len(barMsg.date) == 8:   #it's not a unix timestamp it's something like 20150812 (YYYYMMDD) which means this was a daily bar
                date = datetime.datetime.strptime(barMsg.date,'%Y%m%d')

                
                date = date + offset
                date = tz.localize(date)
                ts = int((date - datetime.datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds()) #probably going to have timezone issues

            else:
                ts = int(barMsg.date)
            startDateTime = dt.localize(datetime.datetime.fromtimestamp(ts,tz),tz)
            self.__currentBarStamp = ts
            return bar.BasicBar(startDateTime, float(barMsg.open), float(barMsg.high), float(barMsg.low), float(barMsg.close), int(barMsg.volume), None, frequency)
        except:
            return None
        
        

        


    def __requestWarmupBars(self):
        #work out what duration and barSize to use

        if self.__frequency < bar.Frequency.DAY:
            barSize = "%d min" % (self.__frequency / bar.Frequency.MINUTE)
            #make it mins for anything greater than a minute
            if self.__frequency > bar.Frequency.MINUTE:
                barSize += "s"
        else:
            barSize = "1 day"

        #duration

        if self.__frequency == bar.Frequency.DAY:
            lookbackDuration = "%d D" % self.__numWarmupBars
        else:
            lookbackDuration = "%d S" % (self.__numWarmupBars * self.__frequency)

        for tickId in range(len(self.__contracts)):
            self.__ib.reqHistoricalData(tickId,
                                          self.__contracts[tickId],
                                          '',
                                          lookbackDuration,       #how far back to go
                                          barSize,      #bar size
                                          'TRADES',
                                          1,
                                          2)

    #adds whatever bars we have to queue and requests new ones so bars can go missing here
    def __requestBars(self):

        #push old bars into queue if any remaining - this might cause problems - commenting out to determine if this is the cause
        '''
        if len(self.__currentBar) > 0:
            bars = bar.Bars(self.__currentBar)
            self.__queue.put(bars)
        '''
        self.__currentBar = {}


        #what are our duration and frequency settings
        if self.__frequency < bar.Frequency.DAY:
            barSize = "%d min" % (self.__frequency / bar.Frequency.MINUTE)
            #make it mins for anything greater than a minute
            if self.__frequency > bar.Frequency.MINUTE:
                barSize += "s"
        else:
            barSize = "1 day"

        #duration

        if self.__frequency == bar.Frequency.DAY:
            lookbackDuration = "1 D"
        else:
            lookbackDuration = "%d S" % (self.__frequency)                

        for tickId in range(len(self.__contracts)):
            #seems no matter what we do we might end up with a couple of bars of data whether we set an end date/time or not
            #need to handle this by ignoring first bars
            
            if self.__lastBarStamp == 0:
                endDate = ''
            else:
                #%z
                #endDate = time.strftime("%Y%m%d %H:%M:%S GMT", time.gmtime(self.__lastBarStamp + (self.__frequency * 2)-1))   
                endDate = time.strftime("%Y%m%d %H:%M:%S GMT", time.gmtime(self.__lastBarStamp + self.__frequency))   
            
            
            #prevent race condition here with threading
            lastBarTS = self.__lastBarStamp 

            self.__ib.reqHistoricalData(tickId,
                                          self.__contracts[tickId],
                                          '',
                                          lookbackDuration,       #how far back to go
                                          barSize,      #bar size
                                          'TRADES',
                                          1,
                                          2)
            
        #start the timer and do it all over again 
        if not self.__synchronised:
            delay = self.__calculateSyncDelay(self.__lastBarStamp)
            self.__synchronised = True
        else:
            delay = self.__frequency

        #print "Sleeping for %d seconds for next bar" % delay
        self.__timer = threading.Timer(delay,self.__requestBars)
        self.__timer.daemon = True
        self.__timer.start()

    def __disconnectHandler(self,msg):
        self.__ib.reconnect()


    def __debugHandler(self,msg):
        if self.__debug:
            print(msg)

    def __errorHandler(self,msg):
        if self.__debug:
            print(msg)

    def __historicalBarsHandler(self,msg):
        '''
        deal with warmup bars first then switch to requesting real time bars. Make sure you deal with end of bars properly and cross fingers there's no loss of data
        '''

        #we get one stock per message here so we need to build a set of bars and only add to queue when all quotes received for all stocks
        #if we ever miss one this thing is going to completely out of whack and either not return anything or go out of order so we also need to be able to say
        #either send the bar off if we start getting new ones before its complete or drop the bar completely - seems easier at this point to drop
        #print "stock: %s - time %s open %.2f hi %.2f, low %.2f close %.2f volume %.2f" % (self.__instruments[msg.reqId],msg.time, msg.open, msg.high,msg.low,msg.close,msg.volume)
        barDict = {}

        instrument = self.__instruments[msg.reqId]

        stockBar = self.__build_bar(msg, instrument,self.__frequency)

        if self.__inWarmup:

            #non bar means feed has finished or worst case data error but haven't seen one of these yet
            if stockBar == None:
                self.__stockFinishedWarmup[instrument] = True
            else:
                self.__warmupBars[instrument].append(stockBar)
                #prevents duplicate bar error when moving to live mode
                if stockBar != None and int(msg.date) > self.__lastBarStamp:
                    self.__lastBarStamp = int(msg.date)
            
            finishedWarmup = True
            for stock in self.__stockFinishedWarmup:
                if self.__stockFinishedWarmup[stock] == False:
                    finishedWarmup = False

            #all stocks have returned all warmup bars - now we take the n most recent warmup bars and return them in order
            if finishedWarmup:

                #truncate the list to recent
                for stock in self.__warmupBars:
                    self.__warmupBars[stock] = self.__warmupBars[stock][-self.__numWarmupBars:]


                for i in range(0,self.__numWarmupBars):
                    currentBars = {}
                    for stock in self.__instruments:
                        currentBars[stock] = self.__warmupBars[stock][i]


                    #push bars onto queue
                    bars = bar.Bars(currentBars)
                    self.__queue.put(bars)

                #mark the warmup as finished and go to normal bar request mode
                #TODO - potentially we may need to use the last bar to work out the end date for the bars - last bar date + frequency 
                self.__inWarmup = False

                #sync ourselves to the server's pace
                #and ensure we're requesting the bars as soon as they are available (10 second lag added on purpose to allow IB to catchup) rather than any lag caused by startup timing
                
                '''
                if stockBar != None and int(msg.date) > self.__lastBarStamp:
                    lastBarStamp = int(msg.date) 
                else:
                    lastBarStamp = self.__lastBarStamp
                '''

                delay = self.__calculateSyncDelay(self.__currentBarStamp)
                self.__synchronised = True

                print("Sleeping for %d seconds for next bar" % delay)
                self.__timer = threading.Timer(delay,self.__requestBars)
                self.__timer.daemon = True
                self.__timer.start()

                #no idea what to do if we missed the end message on the warmup - will never get past here
        else:
            #normal operating mode 
            #below is the live bar code - ignore bars with a date past the last bar stamp
            if stockBar != None and int(msg.date) > self.__lastBarStamp:
                self.__currentBar[self.__instruments[msg.reqId]] = stockBar

            
            #got all bars?
            if len(self.__currentBar) == len(self.__instruments):
                bars = bar.Bars(self.__currentBar)
                self.__queue.put(bars)
                self.__currentBar = {}

                #keep lastBarStamp at latest unix timestamp so we can use it for the enddate of requesthistoricalbars call
                if stockBar != None and int(msg.date) > self.__lastBarStamp:
                    self.__lastBarStamp = int(msg.date)                


    ######################################################################
    # observer.Subject interface
    def __calculateSyncDelay(self,lastBarTS):
        now = int(time.time())
        delay=0
        if lastBarTS > 0:    
            delay = ((lastBarTS + self.__frequency) - now) + 10
        else:
            delay = self.__frequency

        return delay

    #needed for daily bars so we can pick up at the next day's close returns timedelta and timezone
    #time delta is how long after close to next open so 24hrs - opening hours - eg ASX is open 10 - 4 - 8 hours so 24 - 8 is 16
    def __marketCloseTime(self,currency):
        if currency == 'AUD':
            return [datetime.timedelta(hours=16),pytz.timezone('Australia/Sydney')]
        if currency == 'USD':
            return [datetime.timedelta(hours=15,minutes=30),pytz.timezone('America/New_York')]
        if currency == 'GBP':
            return [datetime.timedelta(hours=14,minutes=30),pytz.timezone('Europe/London')]                        


    def start(self):
        pass

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        #TODO might need logic to work out if API has dropped connection here
        return False
        #return self.__thread.stopped()

    def peekDateTime(self):
        return None

    ######################################################################
    # barfeed.BaseBarFeed interface

    def getCurrentDateTime(self):
        return utcnow()

    def barsHaveAdjClose(self):
        return False


    def getNextBars(self):
        ret = None
        try:
            eventData = self.__queue.get(True, LiveFeed.QUEUE_TIMEOUT)
            ret = eventData            
        except Queue.Empty:
            pass
        return ret
