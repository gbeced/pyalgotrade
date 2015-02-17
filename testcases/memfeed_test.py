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

import datetime

import common

from pyalgotrade.feed import memfeed
from pyalgotrade import dispatcher
import feed_test


class MemFeedTestCase(common.TestCase):
    def testBaseFeedInterface(self):
        values = [(datetime.datetime.now() + datetime.timedelta(seconds=i), {"i": i}) for i in xrange(100)]
        feed = memfeed.MemFeed()
        feed.addValues(values)
        feed_test.tstBaseFeedInterface(self, feed)

    def testFeed(self):
        values = [(datetime.datetime.now() + datetime.timedelta(seconds=i), {"i": i}) for i in xrange(100)]

        feed = memfeed.MemFeed()
        feed.addValues(values)

        # Check that the dataseries are available after adding values.
        self.assertTrue("i" in feed)
        self.assertEqual(len(feed["i"]), 0)
        self.assertFalse("dt" in feed)

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed)
        disp.run()

        self.assertTrue("i" in feed)
        self.assertFalse("dt" in feed)
        self.assertEqual(feed["i"][0], 0)
        self.assertEqual(feed["i"][-1], 99)

    def testReset(self):
        key = "i"
        values = [(datetime.datetime.now() + datetime.timedelta(seconds=i), {key: i}) for i in xrange(100)]

        feed = memfeed.MemFeed()
        feed.addValues(values)

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed)
        disp.run()

        keys = feed.getKeys()
        values = feed[key]

        feed.reset()
        disp = dispatcher.Dispatcher()
        disp.addSubject(feed)
        disp.run()
        reloadedKeys = feed.getKeys()
        reloadedValues = feed[key]

        self.assertEqual(keys, reloadedKeys)
        self.assertNotEqual(values, reloadedValues)
        self.assertEqual(len(values), len(reloadedValues))
        for i in range(len(values)):
            self.assertEqual(values[i], reloadedValues[i])
