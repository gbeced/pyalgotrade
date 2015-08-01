# PyAlgoTrade
# ib live broker

'''
TODO:

    - Deal with multiple currencies
    - Test all order types
    - DONE - Test in a live trading situation
    - Deal with problems connecting to API

'''


"""
.. moduleauthor:: Kimble Young <kimbleyoung at yahoo dot com dot au>
"""

import threading
import time
import Queue
import datetime

from pyalgotrade import broker
from pyalgotrade.utils import dt

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message



#build order object from IB API's definition of an open order which has a contract and order attribute
def build_order_from_open_order(openOrder, instrumentTraits):
    #print openOrder
    #order_id = openOrder.order.m_permId   #we use the TWS id for the order rather than our id - not sure this is a good idea but its apparently consistent across sessions - https://www.interactivebrokers.com/en/software/api/apiguide/java/order.htm
    order_id = openOrder.order.m_orderId
    #doesn't seem to be a useable date/time for orders so going to use current time
    #order_time = openOrder.order.m_activeStartTime
    order_time = dt.as_utc(datetime.datetime.now())

    order_type = openOrder.order.m_orderType     #stop, limit, stoplimit, market
    

    order_action = openOrder.order.m_action

    order_amount = openOrder.order.m_totalQuantity
    order_limprice = openOrder.order.m_lmtPrice
    order_auxprice = openOrder.order.m_auxPrice
    contract_symbol = openOrder.contract.m_symbol

    #what else do we need?

    print "ORDER TIME: %s" % order_time
    print "ORDER ID %s" %order_id

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


#Aussie shares only go to 2 or maybe 3 decimal places - US stocks might do 4 but pretty sure it doesn't get finer grained
#later on we may need to do symbol lookup to work this out for now we'll hard code
class EquityTraits(broker.InstrumentTraits):
    def roundQuantity(self, quantity):
        return round(quantity, 4)


class LiveBroker(broker.Broker):
    """An IB live broker.

    :param host: host to connect to default localhost
    :type clientId: string.
    :param host: hostname running your IB API - usually localhost
    :type host: string.
    :param port: port of server running your IB - usually 7496
    :type port: int.
    :param marketOptions: configure asset type, currency and routing - see https://www.interactivebrokers.com/en/software/api/apiguide/java/contract.htm
    :type marketOptions: dict.    
    :param debug: have ibPy spit out all messages to screen (very noisy)
    :type port: bool.


    .. note::
        * Must have read/write access - go into TWS and enable
        * No stop losses, hedging etc - very simple right now 
    """

    def __init__(self, host="localhost", port=7496, marketOptions={'assetType':'STK', 'currency':'GBP','routing': 'SMART'}, debug=False):
        broker.Broker.__init__(self)

        if debug:
            self.__debug = True
        else:
            self.__debug = False

        self.__stop = False

        self.__ib = ibConnection(host=host,port=port,clientId=13679)

        #register all the callback handlers
        self.__ib.registerAll(self.__debugHandler)
        self.__ib.register(self.__accountHandler,'UpdateAccountValue')
        self.__ib.register(self.__portfolioHandler,'UpdatePortfolio')
        self.__ib.register(self.__openOrderHandler, 'OpenOrder')
        self.__ib.register(self.__disconnectHandler,'ConnectionClosed')
        self.__ib.register(self.__nextIdHandler,'NextValidId')

        self.__ib.connect()

        self.__cash = 0
        self.__shares = {}
        self.__activeOrders = {}
        self.__nextOrderId = 0

    def __disconnectHandler(self,msg):
        print "disconnected. reconnecting"
        self.__ib.reconnect()

    #prints all messages from IB API
    def __debugHandler(self,msg): 
        #not sure where to pick this one up from
        if self.__debug: print msg

    def __nextIdHandler(self,msg):
        self.__nextOrderId = msg.orderId
        print "next valid id called %d " % msg.orderId

    #get account messages like cash value etc
    def __accountHandler(self,msg):
        #FYI this is not necessarily USD - probably AUD for me as it's the base currency so if you're buying international stocks need to keep this in mind
        #self.__cash = round(balance.getUSDAvailable(), 2)
        #print msg.key, msg.value , msg.currency
        if msg.key == 'TotalCashBalance' and msg.currency == 'USD':
            self.__cash = round(float(msg.value))

        #if self.__cash > 0:
        #    print "cash %.2f" % self.__cash

    #get portfolio messages - stock, price, purchase price etc
    def __portfolioHandler(self,msg):
        #print "%s:%s" % (msg.contract.m_symbol, msg.contract.m_primaryExch)
        #print msg.position
        self.__shares[msg.contract.m_symbol] = msg.position

    def __openOrderHandler(self,msg):
        #note if you want to test this make sure you actually have an open order otherwise it's never called
        print "__openOrderHandler() called"
        #Remember this is called once per open order so if you have 3 open orders it's called 3 times
        self._registerOrder(build_order_from_open_order(msg, self.getInstrumentTraits(msg.contract.m_symbol)))


    def _registerOrder(self, order):
        #can be registered multiple times - just overwrites
        #assert(order.getId() not in self.__activeOrders)
        assert(order.getId() is not None)
        self.__activeOrders[order.getId()] = order

    def _unregisterOrder(self, order):
        assert(order.getId() in self.__activeOrders)
        assert(order.getId() is not None)
        del self.__activeOrders[order.getId()]


    #subscribes for regular account balances which are sent to portfolio and account handlers
    def refreshAccountBalance(self):
        """Refreshes cash and BTC balance."""

        #self.__stop = True  # Stop running in case of errors.
        print("Retrieving account balance.")
        self.__ib.reqAccountUpdates(1,'')
        


    def refreshOpenOrders(self):
        print("Refreshing open orders")
        self.__ib.reqAllOpenOrders()

        #implemented in the 


    def _startTradeMonitor(self):
        return


    # BEGIN observer.Subject interface
    def start(self):
        self.refreshAccountBalance()
        self.refreshOpenOrders()

    def stop(self):
        self.__stop = True
        self.__ib.disconnect()
        print("Shutting down IB connection")
        #self.__tradeMonitor.stop()

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

    def getActiveOrders(self, instrument=None):
        return self.__activeOrders.values()

    def submitOrder(self, order):
        if order.isInitial():
            # Override user settings based on Bitstamp limitations.
            #order.setAllOrNone(False)
            #order.setGoodTillCanceled(True)

            ibContract = Contract()
            ibOrder = Order()

            ibContract.m_symbol = order.getInstrument()
            ibContract.m_secType = 'STK'
            ibContract.m_currency = 'GBP'
            ibContract.m_exchange = 'SMART'

            ibOrder.m_totalQuantity = order.getQuantity()
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
            elif order.getType() == broker.Order.Type.STOP:
                ibOrder.m_orderType = 'STP'
            elif order.getType() == broker.Order.Type.STOP_LIMIT:
                ibOrder.m_orderType = 'STP LMT'
            

            if order.getAllOrNone() == True:
                ibOrder.m_allOrNone = 1
            else:
                ibOrder.m_allOrNone = 0



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

        return broker.LimitOrder(action, instrument, stopPrice, quantity, instrumentTraits)

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

        #self.__httpClient.cancelOrder(order.getId())
        print "cancelling %s " % order.getId()
        self.__ib.cancelOrder(order.getId())
        self._unregisterOrder(order)
        order.switchState(broker.Order.State.CANCELED)

        # Update cash and shares. - not needed
        #self.refreshAccountBalance()

        # Notify that the order was canceled.
        self.notifyOrderEvent(broker.OrderEvent(order, broker.OrderEvent.Type.CANCELED, "User requested cancellation"))

    # END broker.Broker interface
