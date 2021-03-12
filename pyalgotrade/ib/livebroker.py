"""

PyAlgoTrade
ib live broker

Requires:
- ibPy - https://github.com/blampe/IbPy
- trader work station or IB Gateway - https://www.interactivebrokers.com/en/?f=%2Fen%2Fsoftware%2Fibapi.php&ns=T

Disclaimer: No warranty express or implied is offered for this code

.. moduleauthor:: Kimble Young <kbcool@gmail.com>
"""

import threading
import time
import Queue
import datetime
import random

from pyalgotrade import broker
from pyalgotrade.strategy import position
from pyalgotrade.utils import dt

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message
from pdb import set_trace as bp






#build order object from IB API's definition of an open order which has a contract and order attribute
def build_order_from_open_order(openOrder, instrumentTraits):
    #order_id = openOrder.order.m_permId   #we use the TWS id for the order rather than our id - not sure this is a good idea but its apparently consistent across sessions - https://www.interactivebrokers.com/en/software/api/apiguide/java/order.htm
    order_id = openOrder.order.m_orderId
    #doesn't seem to be a useable date/time for orders so going to use current time
    order_time = dt.as_utc(datetime.datetime.now())

    order_type = openOrder.order.m_orderType     #stop, limit, stoplimit, market
    

    order_action = openOrder.order.m_action

    order_amount = openOrder.order.m_totalQuantity
    order_limprice = openOrder.order.m_lmtPrice
    order_auxprice = openOrder.order.m_auxPrice
    contract_symbol = openOrder.contract.m_symbol


    if order_action == 'BUY':
        action = broker.Order.Action.BUY
    elif order_action == 'SELL':
        action = broker.Order.Action.SELL
    elif order_action == 'SSHORT':
        action = broker.Order.Action.SELL_SHORT
    else:
        raise Exception("Invalid order action")

    if order_type == 'LMT':     #Limit
        ret = broker.LimitOrder(action, contract_symbol, order_limprice, order_amount, instrumentTraits)
    elif order_type == 'MKT':   #Market
        ret = broker.MarketOrder(action, contract_symbol, order_amount, False, instrumentTraits)
    elif order_type == 'MOC':   #Market On Close
        ret = broker.MarketOrder(action, contract_symbol, order_amount, True, instrumentTraits)
    elif order_type == 'STP':   #Stop order
        ret = broker.StopOrder(action, contract_symbol, order_auxprice, order_amount, instrumentTraits)
    elif order_type == 'STP LMT':
        ret = broker.StopLimitOrder(action, contract_symbol, order_auxprice, order_limprice, order_amount, instrumentTraits)
    else:
        #Totally possible if you use pyalgotrade and TWS to manage the same account which is not really a good idea
        raise Exception("Unsupported order type - %s" % order_type)
    

    ret.setSubmitted(order_id, order_time)
    ret.setState(broker.Order.State.ACCEPTED)
    return ret


#roundQuantity is the number of decimal places in an asset quantity - for stocks this can only be a whole number (at least in US/AU/UK etc) and IB also requires an integer so force it
class EquityTraits(broker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return int(quantity)

    #price is to 2 decimal points  (US markets and ASX are two decimal places for stocks exceeding $1)
    def roundPrice(self, price):
        return round(price,2)




class LiveOrder(object):
    def __init__(self):
        self.__accepted = None

    def setAcceptedDateTime(self, dateTime):
        self.__accepted = dateTime

    def getAcceptedDateTime(self):
        return self.__accepted

    # Override to call the fill strategy using the concrete order type.
    # return FillInfo or None if the order should not be filled.
    def process(self, broker_, bar_):
        raise NotImplementedError()


class MarketOrder(broker.MarketOrder, LiveOrder):
    def __init__(self, action, instrument, quantity, onClose, instrumentTraits):
        broker.MarketOrder.__init__(self, action, instrument, quantity, onClose, instrumentTraits)
        LiveOrder.__init__(self)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillMarketOrder(broker_, self, bar_)


class LimitOrder(broker.LimitOrder, LiveOrder):
    def __init__(self, action, instrument, limitPrice, quantity, instrumentTraits):
        broker.LimitOrder.__init__(self, action, instrument, limitPrice, quantity, instrumentTraits)
        LiveOrder.__init__(self)

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillLimitOrder(broker_, self, bar_)


class StopOrder(broker.StopOrder, LiveOrder):
    def __init__(self, action, instrument, stopPrice, quantity, instrumentTraits):
        broker.StopOrder.__init__(self, action, instrument, stopPrice, quantity, instrumentTraits)
        LiveOrder.__init__(self)
        self.__stopHit = False

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopOrder(broker_, self, bar_)

    def setStopHit(self, stopHit):
        self.__stopHit = stopHit

    def getStopHit(self):
        return self.__stopHit


# http://www.sec.gov/answers/stoplim.htm
# http://www.interactivebrokers.com/en/trading/orders/stopLimit.php
class StopLimitOrder(broker.StopLimitOrder, LiveOrder):
    def __init__(self, action, instrument, stopPrice, limitPrice, quantity, instrumentTraits):
        broker.StopLimitOrder.__init__(self, action, instrument, stopPrice, limitPrice, quantity, instrumentTraits)
        LiveOrder.__init__(self)
        self.__stopHit = False  # Set to true when the limit order is activated (stop price is hit)

    def setStopHit(self, stopHit):
        self.__stopHit = stopHit

    def getStopHit(self):
        return self.__stopHit

    def isLimitOrderActive(self):
        # TODO: Deprecated since v0.15. Use getStopHit instead.
        return self.__stopHit

    def process(self, broker_, bar_):
        return broker_.getFillStrategy().fillStopLimitOrder(broker_, self, bar_)





class LiveBroker(broker.Broker):
    """An IB live broker.

    :param host: host to connect to default localhost
    :param host: hostname running your IB API - usually localhost
    :type host: string.
    :param port: port of server running your IB - usually 7496
    :type port: int.
    :param marketOptions: configure asset type, currency and routing - see https://www.interactivebrokers.com/en/software/api/apiguide/java/contract.htm
    :type marketOptions: dict.    
    :param debug: have ibPy spit out all messages to screen (very noisy)
    :type debug: bool.
    :param clientId: client id to use - set this to an integer between 1 and 999 (reserved) if you want to be able modify an order that was submitted on a previous session
    :type clientId: int.


    .. note::
        * Must have read/write access - go into TWS and enable
        * No stop losses, hedging etc - very simple right now 
    """

    def __init__(self, host="localhost", port=7496, marketOptions={'assetType':'STK', 'currency':'GBP','routing': 'SMART'}, debug=False, clientId = None):
        broker.Broker.__init__(self)

        if debug:
            self.__debug = True
        else:
            self.__debug = False

        self.__stop = False

        
        if clientId == None:
            clientId = random.randint(1000,10000)
        

        self.__ib = ibConnection(host=host,port=port,clientId=clientId)
        #self.__ib = ibConnection(host=host,port=port)

        #register all the callback handlers
        self.__ib.registerAll(self.__debugHandler)
        self.__ib.register(self.__accountHandler,'UpdateAccountValue')
        self.__ib.register(self.__portfolioHandler,'UpdatePortfolio')
        self.__ib.register(self.__openOrderHandler, 'OpenOrder')
        #self.__ib.register(self.__positionHandler, 'Position')
        self.__ib.register(self.__disconnectHandler,'ConnectionClosed')
        self.__ib.register(self.__nextIdHandler,'NextValidId')
        self.__ib.register(self.__orderStatusHandler,'OrderStatus')

        self.__ib.connect()

        self.__cash = 0
        self.__shares = {}
        self.__detailedShares = {}
        self.__activeOrders = {}
        self.__nextOrderId = 0
        self.__initialPositions = []


        #parse marketoptions and set defaults
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

        self.refreshAccountBalance()
        self.refreshOpenOrders()

        self.__ib.reqPositions()

        #give ib time to get back to us
        time.sleep(2)

    def __disconnectHandler(self,msg):
        self.__ib.reconnect()

    #prints all messages from IB API
    def __debugHandler(self,msg): 
        if self.__debug: print(msg)

    def __nextIdHandler(self,msg):
        self.__nextOrderId = msg.orderId

    '''
    #build position array from ib object (NOTE: This isn't a pyalgotrade position it's an array with enough details hopefully to build one)
    def build_position_from_open_position(self,msg):
        #return pyalgotrade.strategy.position.LongPosition(self., instrument, stopPrice, None, quantity, goodTillCanceled, allOrNone)
        return {
            'stock': 'STW',
            'shortLong': 'long',
            'quantity': 500,
            'price': 31.63
        }
        pass

    #creates positions and hopefully tells the strategy on startup
    #great for error recovery
    def __positionHandler(self,msg):
        self.__initialPositions.append(self.build_position_from_open_position(msg))
        print "GOT POSITIONS"

    def getInitialPositions(self):
        return self.__initialPositions

    '''

    #listen for orders to be fulfilled or cancelled
    def __orderStatusHandler(self,msg):
        order = self.__activeOrders.get(msg.orderId)
        if order == None:
            return

        #watch out for dupes - don't submit state changes or events if they were already submitted

        eventType = None
        if msg.status == 'Filled' and order.getState() != broker.Order.State.FILLED:
            eventType = broker.OrderEvent.Type.FILLED
            self._unregisterOrder(order)
            #order.setState(broker.Order.State.FILLED)
        if msg.status == 'Submitted' and msg.filled > 0:
            eventType = broker.OrderEvent.Type.PARTIALLY_FILLED
            #may already be partially filled
            #if order.getState() != broker.Order.State.PARTIALLY_FILLED:
            #    order.setState(broker.Order.State.PARTIALLY_FILLED)
        if msg.status == 'Cancelled' and order.getState() != broker.Order.State.CANCELED:
            #self._unregisterOrder(order)
            eventType = broker.OrderEvent.Type.CANCELED
            #order.setState(broker.Order.State.CANCELED)
            self._unregisterOrder(order)
            order.switchState(broker.Order.State.CANCELED)

            # Notify that the order was canceled.
            self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))

        orderExecutionInfo = None
        if eventType == broker.OrderEvent.Type.FILLED or eventType == broker.OrderEvent.Type.PARTIALLY_FILLED:
            orderExecutionInfo = broker.OrderExecutionInfo(msg.avgFillPrice, abs(msg.filled), 0, datetime.datetime.now())

            order.addExecutionInfo(orderExecutionInfo)

            if order.isFilled():
                #self._unregisterOrder(order)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.FILLED, orderExecutionInfo))
            elif order.isPartiallyFilled():
                self.notifyOrderEvent(
                    broker.OrderEvent(order, broker.OrderEvent.Type.PARTIALLY_FILLED, orderExecutionInfo)
                )            
            


    #get account messages like cash value etc
    def __accountHandler(self,msg):
        #FYI this is not necessarily USD - probably AUD for me as it's the base currency so if you're buying international stocks need to keep this in mind
        #self.__cash = round(balance.getUSDAvailable(), 2)
        if msg.key == 'TotalCashBalance' and msg.currency == 'USD':
            self.__cash = round(float(msg.value))

    #get portfolio messages - stock, price, purchase price etc
    def __portfolioHandler(self,msg):
        self.__shares[msg.contract.m_symbol] = msg.position

        self.__detailedShares[msg.contract.m_symbol] = {    'shares': msg.position,             #number of units
                                                            'marketPrice': msg.marketPrice,     #current price on market
                                                            'entryPrice': msg.averageCost,      #cost per unit at acquistion (unfortunately minus commissions)
                                                            'PL': msg.unrealizedPNL             #unrealised profit and loss
                                                        }

    def __openOrderHandler(self,msg):
        #Do nothing now but might want to use this to pick up open orders at start (eg in case of shutdown or crash)
        #note if you want to test this make sure you actually have an open order otherwise it's never called
        #Remember this is called once per open order so if you have 3 open orders it's called 3 times
        
        self._registerOrder(build_order_from_open_order(msg, self.getInstrumentTraits(msg.contract.m_symbol)))

    def _registerOrder(self, order):

        assert(order.getId() is not None)

        #need to make sure order doesn't overwrite as we may lose information
        if order.getId() not in self.__activeOrders:
            self.__activeOrders[order.getId()] = order

    def _unregisterOrder(self, order):
        assert(order.getId() in self.__activeOrders)
        assert(order.getId() is not None)
        del self.__activeOrders[order.getId()]


    #subscribes for regular account balances which are sent to portfolio and account handlers
    def refreshAccountBalance(self):
        self.__ib.reqAccountUpdates(1,'')
        


    def refreshOpenOrders(self):
        self.__ib.reqAllOpenOrders()


    def _startTradeMonitor(self):
        return


    # BEGIN observer.Subject interface
    def start(self):
        return

    def stop(self):
        self.__stop = True
        self.__ib.disconnect()

    def join(self):
        pass

    def eof(self):
        return self.__stop

    def dispatch(self):
        # Switch orders from SUBMITTED to ACCEPTED.
        ordersToProcess = self.__activeOrders.values()
        for order in ordersToProcess:
            if order.isSubmitted():
                order.switchState(broker.Order.State.ACCEPTED)
                self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.ACCEPTED, None))


    def peekDateTime(self):
        # Return None since this is a realtime subject.
        return None

    # END observer.Subject interface

    # BEGIN broker.Broker interface

    def getCash(self, includeShort=True):
        return self.__cash

    def getInstrumentTraits(self, instrument):
        return EquityTraits()

    def getShares(self, instrument):
        return self.__shares.get(instrument, 0)

    def getPositions(self):
        return self.__shares

    #positions is just stock and number of shares - detailed positions includes cost and p/l info
    def getDetailedPositions(self):
        return self.__detailedShares

    def getActiveOrders(self, instrument=None):
        return self.__activeOrders.values()

    def submitOrder(self, order):
        if order.isInitial():

            ibContract = Contract()
            ibOrder = Order()

            ibContract.m_symbol = order.getInstrument()


            ibContract.m_secType = self.__marketOptions['assetType']
            ibContract.m_currency = self.__marketOptions['currency']
            ibContract.m_exchange = self.__marketOptions['routing']

            ibOrder.m_totalQuantity = order.getInstrumentTraits().roundQuantity(order.getQuantity())
            if order.getAction() == (broker.Order.Action.BUY or broker.Order.Action.BUY_TO_COVER):
                ibOrder.m_action = 'BUY'
            elif order.getAction() == broker.Order.Action.SELL:
                ibOrder.m_action = 'SELL'
            elif order.getAction() == broker.Order.Action.SELL_SHORT:
                ibOrder.m_action = 'SELL'

            if order.getType() == broker.Order.Type.MARKET:                
                if order.getFillOnClose():
                    ibOrder.m_orderType = 'MOC'
                else:
                    ibOrder.m_orderType = 'MKT'
            elif order.getType() == broker.Order.Type.LIMIT:
                ibOrder.m_orderType = 'LMT'
                ibOrder.m_lmtPrice = order.getInstrumentTraits().roundPrice(order.getLimitPrice())
            elif order.getType() == broker.Order.Type.STOP:
                ibOrder.m_orderType = 'STP'
                ibOrder.m_auxPrice = order.getInstrumentTraits().roundPrice(order.getStopPrice())
            elif order.getType() == broker.Order.Type.STOP_LIMIT:
                ibOrder.m_orderType = 'STP LMT'
                ibOrder.m_lmtPrice = order.getInstrumentTraits().roundPrice(order.getLimitPrice())
                ibOrder.m_auxPrice = order.getInstrumentTraits().roundPrice(order.getStopPrice())

            

            if order.getAllOrNone() == True:
                ibOrder.m_allOrNone = 1
            else:
                ibOrder.m_allOrNone = 0


            if order.getGoodTillCanceled() == True:
                ibOrder.m_tif = 'GTC'
            else:
                ibOrder.m_tif = 'DAY'

            self.__ib.placeOrder(self.__nextOrderId, ibContract, ibOrder)

            order.setSubmitted(self.__nextOrderId, datetime.datetime.now())
            
            self.__nextOrderId += 1

            self._registerOrder(order)
            # Switch from INITIAL -> SUBMITTED
            # IMPORTANT: Do not emit an event for this switch because when using the position interface
            # the order is not yet mapped to the position and Position.onOrderUpdated will get called.
            order.switchState(broker.Order.State.SUBMITTED)
        else:
            raise Exception("The order was already processed")

    def createMarketOrder(self, action, instrument, quantity, onClose=False):
        #IB doesn't support buy to cover
        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY

        instrumentTraits = self.getInstrumentTraits(instrument)

        return broker.MarketOrder(action, instrument, quantity, onClose, instrumentTraits)

    def createLimitOrder(self, action, instrument, limitPrice, quantity):
        #IB doesn't support buy to cover
        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY

        instrumentTraits = self.getInstrumentTraits(instrument)

        return broker.LimitOrder(action, instrument, limitPrice, quantity, instrumentTraits)

    def createStopOrder(self, action, instrument, stopPrice, quantity):
        #IB doesn't support buy to cover
        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY

        instrumentTraits = self.getInstrumentTraits(instrument)

        return broker.StopOrder(action, instrument, stopPrice, quantity, instrumentTraits)

    def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity):
        #IB doesn't support buy to cover
        if action == broker.Order.Action.BUY_TO_COVER:
            action = broker.Order.Action.BUY

        instrumentTraits = self.getInstrumentTraits(instrument)

        return broker.StopLimitOrder(action, instrument, stopPrice,limitPrice, quantity, instrumentTraits)        

    def cancelOrder(self, order):
        activeOrder = self.__activeOrders.get(order.getId())
        if activeOrder is None:
            raise Exception("The order is not active anymore")
        if activeOrder.isFilled():
            raise Exception("Can't cancel order that has already been filled")

        self.__ib.cancelOrder(order.getId())


        #DO NOT DO THE BELOW:
        '''
        self._unregisterOrder(order)
        order.switchState(broker.Order.State.CANCELED)

        # Update cash and shares. - might not be needed
        self.refreshAccountBalance()

        # Notify that the order was canceled.
        self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))
        '''

    # END broker.Broker interface
