# PyAlgoTrade
# 
# Copyright 2012 Gabriel Martin Becedillas Ruiz
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

import unittest

from pyalgotrade import observer

class ObserverTestCase(unittest.TestCase):
	def testEmitOrder(self):
		handlersData = []

		def handler3():
			handlersData.append(3)

		def handler1():
			handlersData.append(1)

		def handler2():
			handlersData.append(2)

		event = observer.Event()
		event.subscribe(handler1)
		event.subscribe(handler2)
		event.subscribe(handler3)
		event.emit()
		self.assertTrue(handlersData == [1, 2, 3])

		handlersData = []
		event = observer.Event()
		event.subscribe(handler3)
		event.subscribe(handler2)
		event.subscribe(handler1)
		event.emit()
		self.assertTrue(handlersData == [3, 2, 1])

	def testDuplicateHandlers(self):
		def handler1():
			handlersData.append(1)

		handlersData = []
		event = observer.Event()
		event.subscribe(handler1)
		event.subscribe(handler1)
		event.emit()
		self.assertTrue(handlersData == [1])

	def testReentrancy(self):
		handlersData = []
		event = observer.Event()

		def handler2():
			handlersData.append(2)

		def handler1():
			handlersData.append(1)
			event.subscribe(handler2)
			event.subscribe(handler1)

		event.subscribe(handler1)
		event.emit()
		self.assertTrue(handlersData == [1])
		event.emit()
		self.assertTrue(handlersData == [1, 1, 2])
		event.unsubscribe(handler1)
		event.emit()
		self.assertTrue(handlersData == [1, 1, 2, 2])
		event.unsubscribe(handler2)
		event.emit()
		self.assertTrue(handlersData == [1, 1, 2, 2])

def getTestCases():
	ret = []
	ret.append(ObserverTestCase("testEmitOrder"))
	ret.append(ObserverTestCase("testDuplicateHandlers"))
	ret.append(ObserverTestCase("testReentrancy"))
	return ret

