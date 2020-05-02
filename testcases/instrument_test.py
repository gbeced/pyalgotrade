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

from pyalgotrade.instrument import Instrument, build_instrument


@pytest.mark.parametrize("symbol, expected", [
    ("orcl/USD", Instrument("orcl", "USD")),
    ("orcl/EUR", Instrument("orcl", "EUR")),
])
def test_build_instrument(symbol, expected):
    assert build_instrument(symbol) == expected


def test_as_key():
    d = {build_instrument("orcl/USD"): 1}

    assert build_instrument("orcl/USD") in d

    assert build_instrument("orcl/EUR") not in d
    assert build_instrument("aig/USD") not in d

    assert "orcl/USD" in d
    assert "orcl" not in d
    assert "aig" not in d


def test_cmp():
    assert build_instrument("orcl/USD") == build_instrument("orcl/USD")
    assert build_instrument("orcl/ARS") != build_instrument("orcl/USD")


def test_cmp_to_string():
    assert build_instrument("orcl/USD") == "orcl/USD"
    assert build_instrument("orcl/ARS") != "orcl/USD"
