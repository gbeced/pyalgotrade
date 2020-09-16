# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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

import six


PAIR_SEP = "/"


class Instrument(object):
    def __init__(self, symbol, priceCurrency):
        """
        :param symbol: Instrument identifier.
        :param priceCurrency: The price currency.
        """

        assert isinstance(symbol, six.string_types)
        assert isinstance(priceCurrency, six.string_types)
        assert_valid_symbol(symbol)
        assert_valid_currency(priceCurrency)

        self.symbol = symbol
        self.priceCurrency = priceCurrency
        self._str = "%s%s%s" % (symbol, PAIR_SEP, priceCurrency)

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._str

    def _cmp_elements(self, other):
        if isinstance(other, Instrument):
            ret = (self.symbol, self.priceCurrency), (other.symbol, other.priceCurrency)
        else:
            ret = str(self), other
        return ret

    def __eq__(self, other):
        left, right = self._cmp_elements(other)
        return left == right

    def __ne__(self, other):
        left, right = self._cmp_elements(other)
        return left != right

    def __lt__(self, other):
        left, right = self._cmp_elements(other)
        return left < right

    def __le__(self, other):
        left, right = self._cmp_elements(other)
        return left <= right

    def __gt__(self, other):
        left, right = self._cmp_elements(other)
        return left > right

    def __ge__(self, other):
        left, right = self._cmp_elements(other)
        return left >= right

    # def __cmp__(self, other):
    #     if isinstance(other, Instrument):
    #         ret = cmp((self.symbol, self.priceCurrency), (other.symbol, other.priceCurrency))
    #     else:
    #         ret = cmp(str(self), other)
    #     return ret

    def __hash__(self):
        return hash(self._str)


def build_instrument(instrument):
    """
    Helper function to build an instrument.

    :param instrument: A :class:`pyalgotrade.instrument.Instrument` or a string formatted like
        QUOTE_SYMBOL/PRICE_CURRENCY.
    :return: :class:`pyalgotrade.instrument.Instrument`.
    """

    if isinstance(instrument, Instrument):
        return instrument

    assert isinstance(instrument, six.string_types), "Invalid instrument %s" % instrument
    parts = instrument.split(PAIR_SEP)
    if len(parts) != 2:
        raise Exception("Invalid instrument format {}".format(instrument))
    return Instrument(parts[0], parts[1])


def assert_valid_symbol(symbol):
    assert isinstance(symbol, six.string_types)
    assert PAIR_SEP not in symbol, "symbol expected but received {}".format(symbol)


def assert_valid_currency(currency):
    assert isinstance(currency, six.string_types)
    assert PAIR_SEP not in currency, "currency expected but received {}".format(currency)
