# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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


class Event(object):
    def __init__(self):
        self.__handlers = []
        self.__toSubscribe = []
        self.__toUnsubscribe = []
        self.__emitting = False

    def __applyChanges(self):
        if len(self.__toSubscribe):
            for handler in self.__toSubscribe:
                if handler not in self.__handlers:
                    self.__handlers.append(handler)
            self.__toSubscribe = []

        if len(self.__toUnsubscribe):
            for handler in self.__toUnsubscribe:
                self.__handlers.remove(handler)
            self.__toUnsubscribe = []

    def subscribe(self, handler):
        if self.__emitting:
            self.__toSubscribe.append(handler)
        elif handler not in self.__handlers:
            self.__handlers.append(handler)

    def unsubscribe(self, handler):
        if self.__emitting:
            self.__toUnsubscribe.append(handler)
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

    # This may raise.
    @abc.abstractmethod
    def start(self):
        raise NotImplementedError()

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
        raise NotImplementedError()

    def getDispatchPriority(self):
        # Returns a number (or None) used to sort subjects within the dispatch queue.
        # The return value should never change.
        return None
