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

import abc

from pyalgotrade import dispatchprio


class Event(object):
    def __init__(self):
        self.__handlers = set()
        self.__changes = []
        self.__emitting = False

    def __applyChanges(self):
        if self.__changes:
            for verb, arg in self.__changes:
                verb(arg)

    def subscribe(self, handler):
        if self.__emitting:
            self.__changes.append((self.__handlers.add, handler))
        else:
            self.__handlers.add(handler)

    def unsubscribe(self, handler):
        if self.__emitting:
            self.__changes.append((self.__handlers.difference_update, {handler}))
        else:
            self.__handlers.remove(handler)

    def emit(self, *args, **kwargs):
        try:
            self.__emitting = True
            for handler in self.__handlers:
                handler(*args, **kwargs)
        finally:
            self.__emitting = False
            self.__applyChanges()


class Subject(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.__dispatchPrio = dispatchprio.LAST

    # This may raise.
    @abc.abstractmethod
    def start(self):
        pass

    # This should not raise.
    @abc.abstractmethod
    def stop(self):
        raise NotImplementedError()

    # This should not raise.
    @abc.abstractmethod
    def join(self):
        raise NotImplementedError()

    # Return True if there are not more events to dispatch.
    @abc.abstractmethod
    def eof(self):
        raise NotImplementedError()

    # Dispatch events. If True is returned, it means that at least one event was dispatched.
    @abc.abstractmethod
    def dispatch(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def peekDateTime(self):
        # Return the datetime for the next event.
        # This is needed to properly synchronize non-realtime subjects.
        # Return None since this is a realtime subject.
        raise NotImplementedError()

    def getDispatchPriority(self):
        # Returns a priority used to sort subjects within the dispatch queue.
        # The return value should never change once this subject is added to the dispatcher.
        return self.__dispatchPrio

    def setDispatchPriority(self, dispatchPrio):
        self.__dispatchPrio = dispatchPrio

    def onDispatcherRegistered(self, dispatcher):
        # Called when the subject is registered with a dispatcher.
        pass
