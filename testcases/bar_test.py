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

import datetime
import pickle

from . import common

from pyalgotrade import bar


class BasicBarTestCase(common.TestCase):
    def testInvalidConstruction(self):
        with self.assertRaises(Exception):
            bar.BasicBar(datetime.datetime.now(), 2, 1, 1, 1, 1, 1, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            bar.BasicBar(datetime.datetime.now(), 1, 1, 1, 2, 1, 1, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            bar.BasicBar(datetime.datetime.now(), 1, 2, 1.5, 1, 1, 1, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            bar.BasicBar(datetime.datetime.now(), 2, 2, 1.5, 1, 1, 1, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            bar.BasicBar(datetime.datetime.now(), 1, 1, 1.5, 1, 1, 1, bar.Frequency.DAY)

    def testTypicalPrice(self):
        b = bar.BasicBar(datetime.datetime.now(), 2, 3, 1, 2.1, 10, 5, bar.Frequency.DAY)
        self.assertEqual(b.getTypicalPrice(), (3 + 1 + 2.1) / 3)

    def testGetPrice(self):
        b = bar.BasicBar(datetime.datetime.now(), 2, 3, 1, 2.1, 10, 5, bar.Frequency.DAY)
        self.assertEqual(b.getPrice(), b.getClose())
        b.setUseAdjustedValue(True)
        self.assertEqual(b.getPrice(), b.getAdjClose())

    def testPickle(self):
        b1 = bar.BasicBar(datetime.datetime.now(), 2, 3, 1, 2.1, 10, 5, bar.Frequency.DAY)
        b2 = pickle.loads(pickle.dumps(b1))
        self.assertEqual(b1.getDateTime(), b2.getDateTime())
        self.assertEqual(b1.getOpen(), b2.getOpen())
        self.assertEqual(b1.getHigh(), b2.getHigh())
        self.assertEqual(b1.getLow(), b2.getLow())
        self.assertEqual(b1.getClose(), b2.getClose())
        self.assertEqual(b1.getVolume(), b2.getVolume())
        self.assertEqual(b1.getAdjClose(), b2.getAdjClose())
        self.assertEqual(b1.getFrequency(), b2.getFrequency())
        self.assertEqual(b1.getPrice(), b2.getPrice())
        self.assertEqual(b1.getOpen(True), b2.getOpen(True))
        self.assertEqual(b1.getHigh(True), b2.getHigh(True))
        self.assertEqual(b1.getLow(True), b2.getLow(True))
        self.assertEqual(b1.getClose(True), b2.getClose(True))

    def testNoAdjClose(self):
        b = bar.BasicBar(datetime.datetime.now(), 2, 3, 1, 2.1, 10, None, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            b.setUseAdjustedValue(True)
        with self.assertRaises(Exception):
            b.getOpen(True)
        with self.assertRaises(Exception):
            b.getHigh(True)
        with self.assertRaises(Exception):
            b.getLow(True)
        with self.assertRaises(Exception):
            b.getClose(True)


class BarsTestCase(common.TestCase):
    def testEmptyDict(self):
        with self.assertRaises(Exception):
            bar.Bars({})

    def testInvalidDateTimes(self):
        b1 = bar.BasicBar(datetime.datetime.now(), 2, 3, 1, 2.1, 10, 5, bar.Frequency.DAY)
        b2 = bar.BasicBar(datetime.datetime.now() + datetime.timedelta(days=1), 2, 3, 1, 2.1, 10, 5, bar.Frequency.DAY)
        with self.assertRaises(Exception):
            bar.Bars({"a": b1, "b": b2})

    def testBasic(self):
        dt = datetime.datetime.now()
        b1 = bar.BasicBar(dt, 1, 1, 1, 1, 10, 1, bar.Frequency.DAY)
        b2 = bar.BasicBar(dt, 2, 2, 2, 2, 10, 2, bar.Frequency.DAY)
        bars = bar.Bars({"a": b1, "b": b2})
        self.assertEqual(bars["a"].getClose(), 1)
        self.assertEqual(bars["b"].getClose(), 2)
        self.assertTrue("a" in bars)
        self.assertEqual(list(bars.items()), [("a", b1), ("b", b2)])
        self.assertEqual(list(bars.keys()), ["a", "b"])
        self.assertEqual(bars.getInstruments(), ["a", "b"])
        self.assertEqual(bars.getDateTime(), dt)
        self.assertEqual(bars.getBar("a").getClose(), 1)
