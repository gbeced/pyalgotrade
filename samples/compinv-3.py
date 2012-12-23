import csv
import datetime
import os

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import strategy
from pyalgotrade import broker

class OrdersFile:
	def __init__(self, ordersFile):
		self.__orders = {}
		self.__firstDate = None
		self.__lastDate = None
		self.__instruments = []

		# Load orders from the file.
		reader = csv.DictReader(open(ordersFile, "r"), fieldnames=["year", "month", "day", "symbol", "action", "qty"])
		for row in reader:
			dateTime = datetime.datetime(int(row["year"]), int(row["month"]), int(row["day"]))
			self.__orders.setdefault(dateTime, [])
			order = (row["symbol"], row["action"], int(row["qty"]))
			self.__orders[dateTime].append(order)

			# As we process the file, store instruments, first date, and last date.
			if row["symbol"] not in self.__instruments:
				self.__instruments.append(row["symbol"])

			if self.__firstDate == None:
				self.__firstDate = dateTime
			else:
				self.__firstDate = min(self.__firstDate, dateTime)

			if self.__lastDate == None:
				self.__lastDate = dateTime
			else:
				self.__lastDate = max(self.__lastDate, dateTime)

	def getFirstDate(self):
		return self.__firstDate

	def getLastDate(self):
		return self.__lastDate

	def getInstruments(self):
		return self.__instruments

	def getOrders(self, dateTime):
		return self.__orders.get(dateTime, [])

class MyStrategy(strategy.Strategy):
	def __init__(self, feed, cash, ordersFile):
		# Suscribe to the feed bars event before the broker just to place the orders properly.
		feed.getNewBarsEvent().subscribe(self.__onBarsBeforeBroker)
		strategy.Strategy.__init__(self, feed, cash)
		self.__ordersFile = ordersFile
		# We wan't to use adjusted close prices instead of close.
		self.getBroker().setUseAdjustedValues(True)
		# We will allow buying more shares than cash allows.
		self.getBroker().setAllowNegativeCash(True)

	def __onBarsBeforeBroker(self, bars):
		for instrument, action, quantity in self.__ordersFile.getOrders(bars.getDateTime()):
			if action.lower() == "buy":
				action = broker.Order.Action.BUY
			else:
				action = broker.Order.Action.SELL
			o = self.getBroker().createMarketOrder(action, instrument, quantity, onClose=True)
			self.getBroker().placeOrder(o)

	def onOrderUpdated(self, order):
		execInfo = order.getExecutionInfo()
		if execInfo:
			pass
		else:
			raise Exception("Order canceled. Ran out of cash ?")

	def onBars(self, bars):
		portfolioValue = self.getBroker().getValue()
		print "%s: Portfolio value: $%.2f" % (bars.getDateTime(), portfolioValue)

def main():
	# Load the orders file.
	ordersFile = OrdersFile("compinv-3-orders.csv")
	print "First date", ordersFile.getFirstDate()
	print "Last date", ordersFile.getLastDate()
	print "Symbols", ordersFile.getInstruments()

	# Load the data from QSTK storage. QS environment variable has to be defined.
	feed = yahoofeed.Feed()
	feed.setBarFilter(csvfeed.DateRangeFilter(ordersFile.getFirstDate(), ordersFile.getLastDate()))
	feed.setDailyBarTime(datetime.time(0, 0, 0)) # This is to match the dates loaded with the ones in the orders file.
	for symbol in ordersFile.getInstruments():
		feed.addBarsFromCSV(symbol, os.path.join(os.getenv("QS"), "QSData", "Yahoo", symbol + ".csv"))

	# Run the strategy.
	cash = 1000000
	strat = MyStrategy(feed, cash, ordersFile)
	strat.run()

main()

