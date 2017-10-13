# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import abc

from pyalgotrade import broker
import pyalgotrade.bar
from . import slippage


# Returns the trigger price for a Limit or StopLimit order, or None if the limit price was not yet penetrated.
def get_limit_price_trigger(action, limitPrice, useAdjustedValues, bar):
    ret = None
    open_ = bar.getOpen(useAdjustedValues)
    high = bar.getHigh(useAdjustedValues)
    low = bar.getLow(useAdjustedValues)

    # If the bar is below the limit price, use the open price.
    # If the bar includes the limit price, use the open price or the limit price.
    if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
        if high < limitPrice:
            ret = open_
        elif limitPrice >= low:
            if open_ < limitPrice:  # The limit price was penetrated on open.
                ret = open_
            else:
                ret = limitPrice
    # If the bar is above the limit price, use the open price.
    # If the bar includes the limit price, use the open price or the limit price.
    elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
        if low > limitPrice:
            ret = open_
        elif limitPrice <= high:
            if open_ > limitPrice:  # The limit price was penetrated on open.
                ret = open_
            else:
                ret = limitPrice
    else:  # Unknown action
        assert(False)
    return ret


# Returns the trigger price for a Stop or StopLimit order, or None if the stop price was not yet penetrated.
def get_stop_price_trigger(action, stopPrice, useAdjustedValues, bar):
    ret = None
    open_ = bar.getOpen(useAdjustedValues)
    high = bar.getHigh(useAdjustedValues)
    low = bar.getLow(useAdjustedValues)

    # If the bar is above the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    if action in [broker.Order.Action.BUY, broker.Order.Action.BUY_TO_COVER]:
        if low > stopPrice:
            ret = open_
        elif stopPrice <= high:
            if open_ > stopPrice:  # The stop price was penetrated on open.
                ret = open_
            else:
                ret = stopPrice
    # If the bar is below the stop price, use the open price.
    # If the bar includes the stop price, use the open price or the stop price. Whichever is better.
    elif action in [broker.Order.Action.SELL, broker.Order.Action.SELL_SHORT]:
        if high < stopPrice:
            ret = open_
        elif stopPrice >= low:
            if open_ < stopPrice:  # The stop price was penetrated on open.
                ret = open_
            else:
                ret = stopPrice
    else:  # Unknown action
        assert(False)

    return ret


class FillInfo(object):
    def __init__(self, price, quantity):
        self.__price = price
        self.__quantity = quantity

    def getPrice(self):
        return self.__price

    def getQuantity(self):
        return self.__quantity


class FillStrategy(object, metaclass=abc.ABCMeta):
    """Base class for order filling strategies for the backtester."""

    def onBars(self, broker_, bars):
        """
        Override (optional) to get notified when the broker is about to process new bars.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param bars: The current bars.
        :type bars: :class:`pyalgotrade.bar.Bars`
        """
        pass

    def onOrderFilled(self, broker_, order):
        """
        Override (optional) to get notified when an order was filled, or partially filled.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param order: The order filled.
        :type order: :class:`pyalgotrade.broker.Order`
        """
        pass

    @abc.abstractmethod
    def fillMarketOrder(self, broker_, order, bar):
        """Override to return the fill price and quantity for a market order or None if the order can't be filled
        at the given time.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param order: The order.
        :type order: :class:`pyalgotrade.broker.MarketOrder`
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillLimitOrder(self, broker_, order, bar):
        """Override to return the fill price and quantity for a limit order or None if the order can't be filled
        at the given time.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param order: The order.
        :type order: :class:`pyalgotrade.broker.LimitOrder`
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillStopOrder(self, broker_, order, bar):
        """Override to return the fill price and quantity for a stop order or None if the order can't be filled
        at the given time.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopOrder`
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def fillStopLimitOrder(self, broker_, order, bar):
        """Override to return the fill price and quantity for a stop limit order or None if the order can't be filled
        at the given time.

        :param broker_: The broker.
        :type broker_: :class:`Broker`
        :param order: The order.
        :type order: :class:`pyalgotrade.broker.StopLimitOrder`
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`
        :rtype: A :class:`FillInfo` or None if the order should not be filled.
        """
        raise NotImplementedError()


class DefaultStrategy(FillStrategy):
    """
    Default fill strategy.

    :param volumeLimit: The proportion of the volume that orders can take up in a bar. Must be > 0 and <= 1.
        If None, then volume limit is not checked.
    :type volumeLimit: float

    This strategy works as follows:

    * A :class:`pyalgotrade.broker.MarketOrder` is always filled using the open/close price.
    * A :class:`pyalgotrade.broker.LimitOrder` will be filled like this:
        * If the limit price was penetrated with the open price, then the open price is used.
        * If the bar includes the limit price, then the limit price is used.
        * Note that when buying the price is penetrated if it gets <= the limit price, and when selling the price
          is penetrated if it gets >= the limit price
    * A :class:`pyalgotrade.broker.StopOrder` will be filled like this:
        * If the stop price was penetrated with the open price, then the open price is used.
        * If the bar includes the stop price, then the stop price is used.
        * Note that when buying the price is penetrated if it gets >= the stop price, and when selling the price
          is penetrated if it gets <= the stop price
    * A :class:`pyalgotrade.broker.StopLimitOrder` will be filled like this:
        * If the stop price was penetrated with the open price, or if the bar includes the stop price, then the limit
          order becomes active.
        * If the limit order is active:
            * If the limit order was activated in this same bar and the limit price is penetrated as well, then the
              best between the stop price and the limit fill price (as described earlier) is used.
            * If the limit order was activated at a previous bar then the limit fill price (as described earlier)
              is used.

    .. note::
        * This is the default strategy used by the Broker.
        * It uses :class:`pyalgotrade.broker.slippage.NoSlippage` slippage model by default.
        * If volumeLimit is 0.25, and a certain bar's volume is 100, then no more than 25 shares can be used by all
          orders that get processed at that bar.
        * If using trade bars, then all the volume from that bar can be used.
    """

    def __init__(self, volumeLimit=0.25):
        super(DefaultStrategy, self).__init__()
        self.__volumeLeft = {}
        self.__volumeUsed = {}
        self.setVolumeLimit(volumeLimit)
        self.setSlippageModel(slippage.NoSlippage())

    def onBars(self, broker_, bars):
        volumeLeft = {}

        for instrument in bars.getInstruments():
            bar = bars[instrument]
            # Reset the volume available for each instrument.
            if bar.getFrequency() == pyalgotrade.bar.Frequency.TRADE:
                volumeLeft[instrument] = bar.getVolume()
            elif self.__volumeLimit is not None:
                # We can't round here because there is no order to request the instrument traits.
                volumeLeft[instrument] = bar.getVolume() * self.__volumeLimit
            # Reset the volume used for each instrument.
            self.__volumeUsed[instrument] = 0.0

        self.__volumeLeft = volumeLeft

    def getVolumeLeft(self):
        return self.__volumeLeft

    def getVolumeUsed(self):
        return self.__volumeUsed

    def onOrderFilled(self, broker_, order):
        # Update the volume left.
        if self.__volumeLimit is not None:
            # We round the volume left here becuase it was not rounded when it was initialized.
            volumeLeft = order.getInstrumentTraits().roundQuantity(self.__volumeLeft[order.getInstrument()])
            fillQuantity = order.getExecutionInfo().getQuantity()
            assert volumeLeft >= fillQuantity, \
                "Invalid fill quantity %s. Not enough volume left %s" % (fillQuantity, volumeLeft)
            self.__volumeLeft[order.getInstrument()] = order.getInstrumentTraits().roundQuantity(
                volumeLeft - fillQuantity
            )

        # Update the volume used.
        self.__volumeUsed[order.getInstrument()] = order.getInstrumentTraits().roundQuantity(
            self.__volumeUsed[order.getInstrument()] + order.getExecutionInfo().getQuantity()
        )

    def setVolumeLimit(self, volumeLimit):
        """
        Set the volume limit.

        :param volumeLimit: The proportion of the volume that orders can take up in a bar. Must be > 0 and <= 1.
            If None, then volume limit is not checked.
        :type volumeLimit: float
        """

        if volumeLimit is not None:
            assert volumeLimit > 0 and volumeLimit <= 1, "Invalid volume limit"
        self.__volumeLimit = volumeLimit

    def setSlippageModel(self, slippageModel):
        """
        Set the slippage model to use.

        :param slippageModel: The slippage model.
        :type slippageModel: :class:`pyalgotrade.broker.slippage.SlippageModel`
        """

        self.__slippageModel = slippageModel

    def __calculateFillSize(self, broker_, order, bar):
        ret = 0

        # If self.__volumeLimit is None then allow all the order to get filled.
        if self.__volumeLimit is not None:
            maxVolume = self.__volumeLeft.get(order.getInstrument(), 0)
            maxVolume = order.getInstrumentTraits().roundQuantity(maxVolume)
        else:
            maxVolume = order.getRemaining()

        if not order.getAllOrNone():
            ret = min(maxVolume, order.getRemaining())
        elif order.getRemaining() <= maxVolume:
            ret = order.getRemaining()

        return ret

    def fillMarketOrder(self, broker_, order, bar):
        # Calculate the fill size for the order.
        fillSize = self.__calculateFillSize(broker_, order, bar)
        if fillSize == 0:
            broker_.getLogger().debug(
                "Not enough volume to fill %s market order [%s] for %s share/s" % (
                    order.getInstrument(),
                    order.getId(),
                    order.getRemaining()
                )
            )
            return None

        # Unless its a fill-on-close order, use the open price.
        if order.getFillOnClose():
            price = bar.getClose(broker_.getUseAdjustedValues())
        else:
            price = bar.getOpen(broker_.getUseAdjustedValues())
        assert price is not None

        # Don't slip prices when the bar represents the trading activity of a single trade.
        if bar.getFrequency() != pyalgotrade.bar.Frequency.TRADE:
            price = self.__slippageModel.calculatePrice(
                order, price, fillSize, bar, self.__volumeUsed[order.getInstrument()]
            )
        return FillInfo(price, fillSize)

    def fillLimitOrder(self, broker_, order, bar):
        # Calculate the fill size for the order.
        fillSize = self.__calculateFillSize(broker_, order, bar)
        if fillSize == 0:
            broker_.getLogger().debug("Not enough volume to fill %s limit order [%s] for %s share/s" % (
                order.getInstrument(), order.getId(), order.getRemaining())
            )
            return None

        ret = None
        price = get_limit_price_trigger(order.getAction(), order.getLimitPrice(), broker_.getUseAdjustedValues(), bar)
        if price is not None:
            ret = FillInfo(price, fillSize)
        return ret

    def fillStopOrder(self, broker_, order, bar):
        ret = None

        # First check if the stop price was hit so the market order becomes active.
        stopPriceTrigger = None
        if not order.getStopHit():
            stopPriceTrigger = get_stop_price_trigger(
                order.getAction(),
                order.getStopPrice(),
                broker_.getUseAdjustedValues(),
                bar
            )
            order.setStopHit(stopPriceTrigger is not None)

        # If the stop price was hit, check if we can fill the market order.
        if order.getStopHit():
            # Calculate the fill size for the order.
            fillSize = self.__calculateFillSize(broker_, order, bar)
            if fillSize == 0:
                broker_.getLogger().debug("Not enough volume to fill %s stop order [%s] for %s share/s" % (
                    order.getInstrument(),
                    order.getId(),
                    order.getRemaining()
                ))
                return None

            # If we just hit the stop price we'll use it as the fill price.
            # For the remaining bars we'll use the open price.
            if stopPriceTrigger is not None:
                price = stopPriceTrigger
            else:
                price = bar.getOpen(broker_.getUseAdjustedValues())
            assert price is not None

            # Don't slip prices when the bar represents the trading activity of a single trade.
            if bar.getFrequency() != pyalgotrade.bar.Frequency.TRADE:
                price = self.__slippageModel.calculatePrice(
                    order, price, fillSize, bar, self.__volumeUsed[order.getInstrument()]
                )
            ret = FillInfo(price, fillSize)
        return ret

    def fillStopLimitOrder(self, broker_, order, bar):
        ret = None

        # First check if the stop price was hit so the limit order becomes active.
        stopPriceTrigger = None
        if not order.getStopHit():
            stopPriceTrigger = get_stop_price_trigger(
                order.getAction(),
                order.getStopPrice(),
                broker_.getUseAdjustedValues(),
                bar
            )
            order.setStopHit(stopPriceTrigger is not None)

        # If the stop price was hit, check if we can fill the limit order.
        if order.getStopHit():
            # Calculate the fill size for the order.
            fillSize = self.__calculateFillSize(broker_, order, bar)
            if fillSize == 0:
                broker_.getLogger().debug("Not enough volume to fill %s stop limit order [%s] for %s share/s" % (
                    order.getInstrument(),
                    order.getId(),
                    order.getRemaining()
                ))
                return None

            price = get_limit_price_trigger(
                order.getAction(),
                order.getLimitPrice(),
                broker_.getUseAdjustedValues(),
                bar
            )
            if price is not None:
                # If we just hit the stop price, we need to make additional checks.
                if stopPriceTrigger is not None:
                    if order.isBuy():
                        # If the stop price triggered is lower than the limit price, then use that one.
                        # Else use the limit price.
                        price = min(stopPriceTrigger, order.getLimitPrice())
                    else:
                        # If the stop price triggered is greater than the limit price, then use that one.
                        # Else use the limit price.
                        price = max(stopPriceTrigger, order.getLimitPrice())

                ret = FillInfo(price, fillSize)

        return ret
