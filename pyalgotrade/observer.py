# PyAlgoTrade
# 
# Copyright 2011 Gabriel Martin Becedillas Ruiz
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

class Event:
	def __init__(self):
		self.__handlers = []
		self.__toSubscribe = []
		self.__toUnsubscribe = []
		self.__emitting = False

	def __applyChanges(self):
		for handler in self.__toSubscribe:
			if handler not in self.__handlers:
				self.__handlers.append(handler)
		for handler in self.__toUnsubscribe:
			self.__handlers.remove(handler)

		self.__toSubscribe = []
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

	def emit(self, *parameters):
		self.__emitting = True
		for handler in self.__handlers:
			handler(*parameters)
		self.__emitting = False
		self.__applyChanges()

