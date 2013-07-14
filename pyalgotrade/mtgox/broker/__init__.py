# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

from pyalgotrade import broker
from pyalgotrade.broker import backtesting

class BacktestingBroker(backtesting.Broker):
	"""A backtesting broker.

	:param cash: The initial amount of cash.
	:type cash: int/float.
	:param barFeed: The bar feed that will provide the bars.
	:type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
	:param commission: An object responsible for calculating order commissions. **If None, a 0.6% trade commision will be used**.
	:type commission: :class:`pyalgotrade.broker.backtesting.Commission`

	.. note::
		Neither stop nor stop limit orders are supported.
	"""

	def __init__(self, cash, barFeed, commission = None):
		if commission is None:
			commission = backtesting.TradePercentage(0.006)
		backtesting.Broker.__init__(self, cash, barFeed, commission)

	def createMarketOrder(self, action, instrument, quantity, onClose = False):
		if action not in [broker.Order.Action.BUY, broker.Order.Action.SELL]:
			raise Exception("Only BUY/SELL orders are supported")
		if instrument != "BTC":
			raise Exception("Only BTC instrument is supported")
		return backtesting.Broker.createMarketOrder(self, action, instrument, quantity, onClose)

	def createLimitOrder(self, action, instrument, limitPrice, quantity): 
		if action not in [broker.Order.Action.BUY, broker.Order.Action.SELL]:
			raise Exception("Only BUY/SELL orders are supported")
		if instrument != "BTC":
			raise Exception("Only BTC instrument is supported")
		return backtesting.Broker.createLimitOrder(self, action, instrument, limitPrice, quantity)

	def createStopOrder(self, action, instrument, stopPrice, quantity): 
		raise Exception("Stop orders are not supported")

	def createStopLimitOrder(self, action, instrument, stopPrice, limitPrice, quantity): 
		raise Exception("Stop limit orders are not supported")

