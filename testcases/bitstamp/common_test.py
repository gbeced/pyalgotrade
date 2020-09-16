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

import pytest

from pyalgotrade.bitstamp import livebroker


@pytest.mark.parametrize("amount, symbol, expected", [
    (0, "USD", 0),
    (1, "USD", 1),
    (1.123, "USD", 1.12),
    (1.1 + 1.1 + 1.1, "USD", 3.3),
    (1.1 + 1.1 + 1.1 - 3.3, "USD", 0),
    (0.00441376, "BTC", 0.00441376),
    (0.004413764, "BTC", 0.00441376),
    (10.004413764123499, "ETH", 10.004413764123499),
])
def test_instrument_traits(amount, symbol, expected):
    traits = livebroker.InstrumentTraits()
    assert traits.round(amount, symbol) == expected
