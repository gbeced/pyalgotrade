# PyAlgoTrade
# 
# Related materials
# Interactive Brokers API:	http://www.interactivebrokers.com/en/software/api/api.htm
# IbPy: http://code.google.com/p/ibpy/ 
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
.. moduleauthor:: Tibor Kiss <tibor.kiss@gmail.com>
"""

import logging

from pyalgotrade import broker

log = logging.getLogger(__name__)

class FlatRateCommission(broker.Commission):
	"""Flat Rate - US API Directed Orders
	Value	         Flat Rate		Minimum Per Order	Maximum Per Order
	< = 500 shares	$0.0131/share		USD 1.30		0.5% of trade value
	> 500 shares	$0.0081/share		USD 1.30		0.5% of trade value
	"""
	def calculate(self, order, price, quantity):
		minPerOrder=1.3
		maxPerOrder=(price * quantity) * 0.005 
		if quantity <= 500:
			flatRate = 0.0131 * quantity
		else:
			flatRate = 0.0081 * quantity

		commission = max(minPerOrder, flatRate)
		commission = min(maxPerOrder, commission)

		log.debug("Flat rate commission: price=%.2f, quantity=%d minPerOrder=%.2f, maxPerOrder=%.4f, flatRate=%.4f. => commission=%.2f" %
				  (price, quantity, minPerOrder, maxPerOrder, flatRate, commission))

		return commission

class Order(broker.Order):
	class OrderType:
			LMT          = 1
			MKT          = 2
			STP          = 3
			STP_LMT      = 4
			TRAIL        = 5

	def __init__(self, action, instrument, orderType, quantity, auxPrice, lmtPrice, tif, goodTillDate): 
			broker.Order.__init__(self, action, instrument, quantity, goodTillCanceled=False)

			self.__orderType = orderType
			self.__auxPrice = auxPrice
			self.__lmtPrice = lmtPrice
			self.__tif = tif
			self.__goodTillDate = goodTillDate

	def getOrderType(self):
		return self.__orderType

	def getAuxPrice(self):
		return self.__auxPrice

	def getLmtPrice(self):
		return self.__lmtPrice
	
	def getTIF(self):
		return self.__tif

	def getGoodTillDate(self):
		return self.__goodTillDate
	
	def cancel(self):
		"""Cancels an accepted order. If the order is filled an Exception is raised."""
		if self.isFilled():
			raise Exception("Can't cancel order that has already been processed")
		# TODO: Need to notify the broker here
		self.__state = Order.State.CANCELED

class Broker(broker.Broker):
	"""Class responsible for forwarding orders to Interactive Brokers Gateway via TWS.

	:param ibConnection: Object responsible to forward requests to TWS.
	:type ibConnection: :class:`IBConnection`
	"""
	def __init__(self, ibConnection):
		self.__ibConnection = ibConnection

		# Query the server for available funds
		self.__cash = self.__ibConnection.getCash()

		# Subscribe for order updates from TWS
		self.__ibConnection.subscribeOrderUpdates(self.__orderUpdate)

		# Local buffer for Orders. Keys are the orderIDs
		self.__orders = {}

		# Call the base's constructor
		broker.Broker.__init__(self, self.__cash)

	def __orderUpdate(self, orderID, instrument, status, filled, remaining, avgFillPrice, lastFillPrice):
		"""Handles order updates from IBConnection. Processes its status and notifies the strategy's __onOrderUpdate()"""

		log.debug('orderUpdate: orderID=%d, instrument=%s, status=%s, filled=%d, remaining=%d, avgFillPrice=%.2f, lastFillPrice=%.2f' % 
				  (orderID, instrument, status, filled, remaining, avgFillPrice, lastFillPrice))

		# Try to look up order (:class:`broker.Order`) from the local buffer
		# It is possible that the orderID is not present in the buffer: the
		# order could been created from another client (e.g. TWS). 
		# In such cases the order update will be ignored.
		try:
			order = self.__orders[orderID]
		except KeyError:
			log.warn("Order is not registered with orderID: %d, ignoring update" % orderID)
			return

		# Check for order status and set our local order accordingly
		if status == 'Cancelled':
			order.cancel()
		elif status == 'PreSubmitted':
			# Skip, we do not have the corresponding state in :class:`broker.Order`
			return
		elif status == 'Filled':
			# Wait until all the stocks are obtained
			if remaining == 0:
				log.info("Order complete: orderID: %d, instrument: %s, filled: %d, avgFillPrice=%.2f, lastFillPrice=%.2f" %
					 (orderID, instrument, status, filled, avgFillPrice, lastFillPrice))

				# Set commission to 0, avgFillPrice contains it anyhow
				orderExecutionInfo = broker.OrderExecutionInfo(avgFillPrice, comission=0, dateTime=None)
				order.setExecuted(orderExecutionInfo)
			else:
				# And signal partial completions
				log.info("Partial order completion: orderID: %d, instrument: %s, filled: %d, remaining: %d, avgFillPrice=%.2f, lastFillPrice=%.2f" %
					 (orderID, instrument, status, filled, remaining, avgFillPrice, lastFillPrice))

		# Notify the listeners
		self.getOrderUpdatedEvent().emit(self, order)


	def getShares(self, instrument):
		"""Returns the number of shares for an instrument."""
		raise Exception("getShares() is not implemented")

	def getCash(self):
		"""Returns the amount of cash."""
		return self.__ibConnection.getCash()
	
	def setCash(self, cash):
		"""Setting cash on real broker account. Quite impossible :)"""
		raise Exception("Setting cash on a real broker account? Please visit your bank.")
	
	def getValue(self, bars):
		"""Returns the portfolio value (cash + shares) for the given bars prices.

		:param bars: The bars to use to calculate share values.
		:type bars: :class:`pyalgotrade.bar.Bars`.
		"""
		raise Exception("getValue() is not implemented")

	def commitOrderExecution(self, order, price, quantity, dateTime):
		"""Tries to commit an order execution. Right now with IB all the orders are passed to the real broker"""
		return True
	
	def placeOrder(self, order):
		"""Submits an order.

		:param order: The order to submit.
		:type order: :class:`Order`.
		"""

		instrument = order.getInstrument()

		# action: Identifies the side. 
		# Valid values are: BUY, SELL, SSHORT
		act = order.getAction()
		if act == Order.Action.BUY:
			action = "BUY"
		elif act == Order.Action.SELL:
			action = "SELL"
		elif act == Order.Action.SELL_SHORT:
			# XXX: SSHORT is not valid for some reason,
			# and SELL seems to work well with short orders.
			#action = "SSHORT"
			action = "SELL"

		auxPrice = order.getAuxPrice() 
		lmtPrice = order.getLmtPrice() 
		
		ot = order.getOrderType()

		if ot == Order.OrderType.MKT:
			orderType = "MKT"
		elif ot == Order.OrderType.LMT:
			orderType = "LMT"
		elif ot == Order.OrderType.STP:
			orderType = "STP"
		elif ot == Order.OrderType.STP_LMT:
			orderType = "STP LMT"
		elif ot == Order.OrderType.TRAIL:
			orderType = "TRAIL"
		else:
			raise Exception("Invalid orderType: %s!"% ot)

		# Setup quantities
		totalQty = order.getQuantity()
		minQty = 0

		goodTillDate = order.getGoodTillDate()

		# The time in force. Valid values are: DAY, GTC, IOC, GTD.
		tif = order.getTIF()

		trailingPct = 0
		trailStopPrice = 0

		transmit = True
		whatif = False
		 
		orderID = self.__ibConnection.createOrder(instrument, action, auxPrice, lmtPrice, orderType, totalQty, minQty,
							  goodTillDate, tif, trailingPct, trailStopPrice, transmit, whatif)

		self.__orders[orderID] = order

		return orderID
	
	def onBars(self, bars):
		"""Originally the broker logic were handled in this method.
		
		We are using a real broker, no need for any code here."""
		pass


# vim: noet:ci:pi:sts=0:sw=4:ts=4
