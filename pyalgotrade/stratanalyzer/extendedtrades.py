# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import stratanalyzer
from pyalgotrade import broker

from pyalgotrade.stratanalyzer import trades
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import extendedpositiontracker

import numpy as np


class ExtendedTradesAnalyzer(trades.Trades):
    """
    An extended :class:`trades.Trades` that in addition to profits
    also records entry/exit prices and dates, as well as the number
    of contracts/shares hold and whether the position was a long or
    short.

    .. note::
        Like the base class this analyzer operates on individual
        completed trades.
    """

    def __init__(self):
        super(ExtendedTradesAnalyzer, self).__init__()
        self.allEnterDates = []
        self.allExitDates = []
        self.allLongFlags = []
        self.allEntryPrices = []
        self.allExitPrices = []
        self.allContracts = []

    def _updateTrades(self, posTracker):
        # The price doesn't matter since the position should be closed.
        price = 0
        assert posTracker.getPosition() == 0
        netProfit = posTracker.getPnL(price)
        netReturn = posTracker.getReturn(price)

        if netProfit > 0:
            self._Trades__profits.append(netProfit)
            self._Trades__positiveReturns.append(netReturn)
            self._Trades__profitableCommissions.append(
                posTracker.getCommissions())
        elif netProfit < 0:
            self._Trades__losses.append(netProfit)
            self._Trades__negativeReturns.append(netReturn)
            self._Trades__unprofitableCommissions.append(
                posTracker.getCommissions())
        else:
            self._Trades__evenTrades += 1
            self._Trades__evenCommissions.append(posTracker.getCommissions())

        self._Trades__all.append(netProfit)
        self._Trades__allReturns.append(netReturn)
        self._Trades__allCommissions.append(posTracker.getCommissions())
        self.allEnterDates.append(posTracker.enteredOn)
        self.allExitDates.append(posTracker.exitedOn)
        self.allLongFlags.append(posTracker.isLong)
        self.allEntryPrices.append(posTracker.entryPrice)
        self.allExitPrices.append(posTracker.exitPrice)
        self.allContracts.append(posTracker.contracts)

        posTracker.reset()

    def _updatePosTracker(self, posTracker, price, commission, quantity,
                          datetime):
        currentShares = posTracker.getPosition()

        if currentShares > 0:  # Current position is long
            if quantity > 0:  # Increase long position
                posTracker.buy(quantity, price, commission)
            else:
                newShares = currentShares + quantity
                if newShares == 0:  # Exit long.
                    posTracker.sell(currentShares, price, commission)
                    posTracker.exitedOn = datetime
                    self._updateTrades(posTracker)
                elif newShares > 0:  # Sell some shares.
                    posTracker.sell(quantity * -1, price, commission)
                else:
                    # Exit long and enter short. Use proportional commissions.
                    proportionalCommission = commission * \
                        currentShares / float(quantity * -1)
                    posTracker.sell(currentShares, price,
                                    proportionalCommission)
                    posTracker.exitedOn = datetime
                    self._updateTrades(posTracker)
                    proportionalCommission = commission * \
                        newShares / float(quantity)
                    posTracker.sell(newShares * -1, price,
                                    proportionalCommission)
                    posTracker.enteredOn = datetime
        elif currentShares < 0:  # Current position is short
            if quantity < 0:  # Increase short position
                posTracker.sell(quantity * -1, price, commission)
            else:
                newShares = currentShares + quantity
                if newShares == 0:  # Exit short.
                    posTracker.buy(currentShares * -1, price, commission)
                    posTracker._exitedOn = datetime
                    self._updateTrades(posTracker)
                elif newShares < 0:  # Re-buy some shares.
                    posTracker.buy(quantity, price, commission)
                else:
                    # Exit short and enter long. Use proportional commissions.
                    proportionalCommission = (
                        commission * currentShares * -1 / float(quantity))
                    posTracker.buy(currentShares * -1, price,
                                   proportionalCommission)
                    posTracker.exitedOn = datetime
                    self._updateTrades(posTracker)
                    proportionalCommission = commission * \
                        newShares / float(quantity)
                    posTracker.buy(newShares, price, proportionalCommission)
                    posTracker.enteredOn = datetime
        elif quantity > 0:
            posTracker.buy(quantity, price, commission)
            posTracker.enteredOn = datetime
        else:
            posTracker.sell(quantity * -1, price, commission)
            posTracker.enteredOn = datetime

    def _onOrderEvent(self, broker_, orderEvent):
        # Only interested in filled or partially filled orders.
        if orderEvent.getEventType() not in (
                broker.OrderEvent.Type.PARTIALLY_FILLED,
                broker.OrderEvent.Type.FILLED):
            return

        order = orderEvent.getOrder()

        # Get or create the tracker for this instrument.
        try:
            posTracker = self._Trades__posTrackers[order.getInstrument()]
        except KeyError:
            posTracker = ExtendedPositionTracker(order.getInstrumentTraits())
            self._Trades__posTrackers[order.getInstrument()] = posTracker

        # Update the tracker for this order.
        execInfo = orderEvent.getEventInfo()
        price = execInfo.getPrice()
        commission = execInfo.getCommission()
        action = order.getAction()
        if action in [broker.Order.Action.BUY,
                      broker.Order.Action.BUY_TO_COVER]:
            quantity = execInfo.getQuantity()
        elif action in [broker.Order.Action.SELL,
                        broker.Order.Action.SELL_SHORT]:
            quantity = execInfo.getQuantity() * -1
        else:  # Unknown action
            assert(False)

        self._updatePosTracker(posTracker, price, commission,
                               quantity, execInfo.getDateTime())

    def attached(self, strat):
        strat.getBroker().getOrderUpdatedEvent().subscribe(self._onOrderEvent)

    def beforeOnBars(self, strat, bars):
        self._bars = bars

        for instrument in bars.keys():
            try:
                posTracker = self._Trades__posTrackers[instrument]
            except KeyError:
                continue

            high = bars[instrument].getHigh()
            low = bars[instrument].getLow()

            posTracker.setHigh(high)
            posTracker.setLow(low)
        pass
