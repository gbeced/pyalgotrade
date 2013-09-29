# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#	http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import unittest
import datetime

from pyalgotrade.feed import memfeed
from pyalgotrade import observer

class MemFeedTestCase(unittest.TestCase):
	def testFeed(self):
		values = [{"dt":datetime.datetime.now() + datetime.timedelta(seconds=i), "i":i} for i in xrange(100)]

		f = memfeed.MemFeed("dt")
		f.addValues(values)
		d = observer.Dispatcher()
		d.addSubject(f)
		d.run()

		self.assertTrue("i" in f)
		self.assertFalse("dt" in f)
		self.assertEquals(f["i"][0], 0)
		self.assertEquals(f["i"][-1], 99)

def getTestCases():
	ret = []

	ret.append(MemFeedTestCase("testFeed"))

	return ret

