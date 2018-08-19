# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import six


@six.add_metaclass(abc.ABCMeta)
class SlippageModel(object):
    """Base class for slippage models.

    .. note::
        This is a base class and should not be used directly.
    """

    @abc.abstractmethod
    def calculatePrice(self, order, price, quantity, bar, volumeUsed):
        """
        Returns the slipped price per share for an order.

        :param order: The order being filled.
        :type order: :class:`pyalgotrade.broker.Order`.
        :param price: The price for each share before slippage.
        :type price: float.
        :param quantity: The amount of shares that will get filled at this time for this order.
        :type quantity: float.
        :param bar: The current bar.
        :type bar: :class:`pyalgotrade.bar.Bar`.
        :param volumeUsed: The volume size that was taken so far from the current bar.
        :type volumeUsed: float.
        :rtype: float.
        """
        raise NotImplementedError()


class NoSlippage(SlippageModel):
    """A no slippage model."""

    def calculatePrice(self, order, price, quantity, bar, volumeUsed):
        return price


class VolumeShareSlippage(SlippageModel):
    """
    A volume share slippage model as defined in Zipline's VolumeShareSlippage model.
    The slippage is calculated by multiplying the price impact constant by the square of the ratio of the order
    to the total volume.

    Check https://www.quantopian.com/help#ide-slippage for more details.

    :param priceImpact: Defines how large of an impact your order will have on the backtester's price calculation.
    :type priceImpact: float.
    """

    def __init__(self, priceImpact=0.1):
        super(VolumeShareSlippage, self).__init__()
        self.__priceImpact = priceImpact

    def calculatePrice(self, order, price, quantity, bar, volumeUsed):
        assert bar.getVolume(), "Can't use 0 volume bars with VolumeShareSlippage"

        totalVolume = volumeUsed + quantity
        volumeShare = totalVolume / float(bar.getVolume())
        impactPct = volumeShare ** 2 * self.__priceImpact
        if order.isBuy():
            ret = price * (1 + impactPct)
        else:
            ret = price * (1 - impactPct)
        return ret
