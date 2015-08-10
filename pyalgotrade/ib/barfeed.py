# Interactive brokers live feed module
# Code snippets here:
#
# https://groups.google.com/forum/#!topic/ibpy-discuss/QQ1rWvasW0Y
# multiple feeds - http://www.mediafire.com/view/47ig9v98bokzajl/getMultipleMarketData.py
# using a python queue - https://groups.google.com/forum/#!topic/ibpy-discuss/5l0LFm1ehpc
#
# IB live bars only gives 5 second bars - implement this first and test then look at queueing up bars and calculating high, low etc for the requested period - day week etc
#
# TODO support different frequencies by resampling bars
# TODO - bars are delayed by one bar frequency - make them trigger immediately - to do this we need to grab date of last bar before requesting next lot of historicla bars and flush bars on date=finished-20150802
# TODO - History - how can we request x bars of history to feed warmup MAs etc
# TEST - currently only does GPB currency stocks - how to specify different currencies, exchanges and instruments (stock, currency etc)

import time
import datetime
import threading
import Queue
import random
import sys


from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade import dataseries
from pyalgotrade import resamplebase
import pyalgotrade.logger
from pyalgotrade.utils import dt
from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message


#does this line work?
#logger = pyalgotrade.logger.getLogger("ib")


def utcnow():
    return dt.as_utc(datetime.datetime.utcnow())


def build_bar(barMsg, identifier,frequency):
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

    try:
        startDateTime = datetime.datetime.fromtimestamp(int(barMsg.date)).strftime("%m/%d/%Y %I:%M:%S %p")
    except:
        return None

    #instrument, exchange = api.parse_instrument_exchange(identifier)
    #startDateTime = api.to_market_datetime(startDateTime, exchange)
    print barMsg

    return bar.BasicBar(startDateTime, float(barMsg.open), float(barMsg.high), float(barMsg.low), float(barMsg.close), int(barMsg.volume), None, frequency)


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
        if self.__frequency not in [60,120,300,900,1800]:
            raise Exception("Please use a frequency of 1,2,5,15,30,60 minutes or 1 day")

        #builds up a list of quotes
        self.__queue = Queue.Queue()
        self.__currentBar = {}

        #keep track of latest timestamp on any bars for requesting next set
        self.__lastBarStamp = 0

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
            #self.__ib.reqRealTimeBars(tickId, stkContract, 5,'MIDPOINT',0)
            #print "subscribing to %s" % self.__instruments[tickId]

        
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
            print "requesting warmup"
            self.__requestWarmupBars()
        else:
            #start the clock
            print "requesting live bars"
            self.__requestBars()
        
        print "__init finished"


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

        #push old bars into queue if any remaining - this might cause problems
        if len(self.__currentBar) > 0:
            bars = bar.Bars(self.__currentBar)
            self.__queue.put(bars)

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
            

            print "requesting %s of data with a bar size of %s for %s using enddate of %s" % (lookbackDuration,barSize,self.__contracts[tickId], endDate)
            
            self.__ib.reqHistoricalData(tickId,
                                          self.__contracts[tickId],
                                          '',
                                          lookbackDuration,       #how far back to go
                                          barSize,      #bar size
                                          'TRADES',
                                          1,
                                          2)
            
        #start the timer and do it all over again
        self.__timer = threading.Timer(self.__frequency,self.__requestBars)
        self.__timer.start()
        print "requested bars"

    def __debugHandler(self,msg):
        if self.__debug:
            print msg

    def __errorHandler(self,msg):
        print("Could not contact IB API check connectivity")

    def __historicalBarsHandler(self,msg):
        '''
        deal with warmup bars first then switch to requesting real time bars. Make sure you deal with end of bars properly and cross fingers there's no loss of data
        '''




        #we get one stock per message here so we need to build a set of bars and only add to queue when all quotes received for all stocks
        #if we ever miss one this thing is going to completely out of whack and either not return anything or go out of order so we also need to be able to say
        #either send the bar off if we start getting new ones before its complete or drop the bar completely - seems easier at this point to drop
        #print "stock: %s - time %s open %.2f hi %.2f, low %.2f close %.2f volume %.2f" % (self.__instruments[msg.reqId],msg.time, msg.open, msg.high,msg.low,msg.close,msg.volume)
        barDict = {}

        stockBar = build_bar(msg, self.__instruments[msg.reqId],self.__frequency)

    

        if self.__inWarmup:
            print "warming up"

            #non bar means feed has finished or worst case data error but haven't seen one of these yet
            if stockBar == None:
                self.__stockFinishedWarmup[self.__instruments[msg.reqId]] = True
                print "bar finished warmup"
            else:
                print "got historical warmup bar"
                self.__warmupBars[self.__instruments[msg.reqId]].append(stockBar)
            
            print self.__stockFinishedWarmup
            finishedWarmup = True
            for stock in self.__stockFinishedWarmup:
                if self.__stockFinishedWarmup[stock] == False:
                    finishedWarmup = False

            #all stocks have returned all warmup bars - now we take the n most recent warmup bars and return them in order
            if finishedWarmup:
                print "finished warmup"

                #truncate the list to recent
                for stock in self.__warmupBars:
                    self.__warmupBars[stock] = self.__warmupBars[stock][-self.__numWarmupBars:]


                for i in range(0,self.__numWarmupBars):
                    print i
                    currentBars = {}
                    for stock in self.__instruments:
                        print "len of bars for stock %s - %d" % (stock,len(self.__warmupBars[stock]))
                        currentBars[stock] = self.__warmupBars[stock][i]


                    #push bars onto queue
                    bars = bar.Bars(currentBars)
                    self.__queue.put(bars)

                #mark the warmup as finished and go to normal bar request mode
                #TODO - potentially we may need to use the last bar to work out the end date for the bars - last bar date + frequency 
                self.__inWarmup = False



                self.__timer = threading.Timer(self.__frequency,self.__requestBars)
                self.__timer.start()
                print "finished warmup and pushed all bars to queue - entering normal bar mode - requesting every %d frequency seconds" % self.__frequency
                #print "not really - uncomment the line above"

            #no idea what to do if we missed the end message on the warmup - will never get past here
        else:
            #normal operating mode 
            #TODO - when all bars flushed through add to queue - looks like it might be happening given we check for all bars below

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

    #todo implement in IB
    def getNextBars(self):
        ret = None
        try:
            eventData = self.__queue.get(True, LiveFeed.QUEUE_TIMEOUT)
            ret = eventData            
        except Queue.Empty:
            pass
        return ret
