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
import copy

import common

from pyalgotrade import observer
from pyalgotrade import dispatcher


class NonRealtimeFeed(observer.Subject):
    def __init__(self, datetimes, priority=None):
        super(NonRealtimeFeed, self).__init__()
        self.__datetimes = datetimes
        self.__event = observer.Event()
        self.__priority = priority

    def getEvent(self):
        return self.__event

    def start(self):
        super(NonRealtimeFeed, self).start()

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        return len(self.__datetimes) == 0

    def dispatch(self):
        ret = True
        self.__event.emit(self.__datetimes.pop(0))
        return ret

    def peekDateTime(self):
        return self.__datetimes[0]

    def getDispatchPriority(self):
        return self.__priority


class RealtimeFeed(observer.Subject):
    def __init__(self, datetimes, priority=None):
        super(RealtimeFeed, self).__init__()
        self.__datetimes = datetimes
        self.__event = observer.Event()
        self.__priority = priority

    def getEvent(self):
        return self.__event

    def start(self):
        super(RealtimeFeed, self).start()

    def stop(self):
        pass

    def join(self):
        pass

    def eof(self):
        return len(self.__datetimes) == 0

    def dispatch(self):
        ret = True
        self.__event.emit(self.__datetimes.pop(0))
        return ret

    def peekDateTime(self):
        return None

    def getDispatchPriority(self):
        return self.__priority


class DispatcherTestCase(common.TestCase):
    def test1NrtFeed(self):
        values = []
        now = datetime.datetime.now()
        datetimes = [now + datetime.timedelta(seconds=i) for i in xrange(10)]
        nrtFeed = NonRealtimeFeed(copy.copy(datetimes))
        nrtFeed.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(nrtFeed)
        disp.run()

        self.assertEqual(values, datetimes)

    def test2NrtFeeds(self):
        values = []
        now = datetime.datetime.now()
        datetimes1 = [now + datetime.timedelta(seconds=i) for i in xrange(10)]
        datetimes2 = [now + datetime.timedelta(seconds=i+len(datetimes1)) for i in xrange(10)]
        nrtFeed1 = NonRealtimeFeed(copy.copy(datetimes1))
        nrtFeed1.getEvent().subscribe(lambda x: values.append(x))
        nrtFeed2 = NonRealtimeFeed(copy.copy(datetimes2))
        nrtFeed2.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(nrtFeed1)
        disp.addSubject(nrtFeed2)
        disp.run()

        self.assertEqual(len(values), len(datetimes1) + len(datetimes2))
        self.assertEqual(values[:len(datetimes1)], datetimes1)
        self.assertEqual(values[len(datetimes1):], datetimes2)

    def test1RtFeed(self):
        values = []
        now = datetime.datetime.now()
        datetimes = [now + datetime.timedelta(seconds=i) for i in xrange(10)]
        nrtFeed = RealtimeFeed(copy.copy(datetimes))
        nrtFeed.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(nrtFeed)
        disp.run()

        self.assertEqual(values, datetimes)

    def test2RtFeeds(self):
        values = []
        now = datetime.datetime.now()
        datetimes1 = [now + datetime.timedelta(seconds=i) for i in xrange(10)]
        datetimes2 = [now + datetime.timedelta(seconds=i+len(datetimes1)) for i in xrange(10)]
        nrtFeed1 = RealtimeFeed(copy.copy(datetimes1))
        nrtFeed1.getEvent().subscribe(lambda x: values.append(x))
        nrtFeed2 = RealtimeFeed(copy.copy(datetimes2))
        nrtFeed2.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(nrtFeed1)
        disp.addSubject(nrtFeed2)
        disp.run()

        self.assertEqual(len(values), len(datetimes1) + len(datetimes2))
        for i in xrange(len(datetimes1)):
            self.assertEqual(values[i*2], datetimes1[i])
            self.assertEqual(values[i*2+1], datetimes2[i])

    def test2Combined(self):
        values = []
        now = datetime.datetime.now()
        datetimes1 = [now + datetime.timedelta(seconds=i) for i in xrange(10)]
        datetimes2 = [now + datetime.timedelta(seconds=i+len(datetimes1)) for i in xrange(10)]
        nrtFeed1 = RealtimeFeed(copy.copy(datetimes1))
        nrtFeed1.getEvent().subscribe(lambda x: values.append(x))
        nrtFeed2 = NonRealtimeFeed(copy.copy(datetimes2))
        nrtFeed2.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(nrtFeed1)
        disp.addSubject(nrtFeed2)
        disp.run()

        self.assertEqual(len(values), len(datetimes1) + len(datetimes2))
        for i in xrange(len(datetimes1)):
            self.assertEqual(values[i*2], datetimes1[i])
            self.assertEqual(values[i*2+1], datetimes2[i])

    def testPriority(self):
        feed4 = RealtimeFeed([], None)
        feed3 = RealtimeFeed([], None)
        feed2 = RealtimeFeed([], 3)
        feed1 = RealtimeFeed([], 0)

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed3)
        disp.addSubject(feed2)
        disp.addSubject(feed1)
        self.assertEqual(disp.getSubjects(), [feed1, feed2, feed3])

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed1)
        disp.addSubject(feed2)
        disp.addSubject(feed3)
        self.assertEqual(disp.getSubjects(), [feed1, feed2, feed3])

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed3)
        disp.addSubject(feed4)
        disp.addSubject(feed2)
        disp.addSubject(feed1)
        self.assertEqual(disp.getSubjects(), [feed1, feed2, feed3, feed4])

    def testDispatchOrder(self):
        values = []
        now = datetime.datetime.now()
        feed1 = NonRealtimeFeed([now], 0)
        feed2 = RealtimeFeed([now + datetime.timedelta(seconds=1)], None)
        feed1.getEvent().subscribe(lambda x: values.append(x))
        feed2.getEvent().subscribe(lambda x: values.append(x))

        disp = dispatcher.Dispatcher()
        disp.addSubject(feed2)
        disp.addSubject(feed1)
        self.assertEqual(disp.getSubjects(), [feed1, feed2])
        disp.run()
        # Check that although feed2 is realtime, feed1 was dispatched before.
        self.assertTrue(values[0] < values[1])


class EventTestCase(common.TestCase):
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
