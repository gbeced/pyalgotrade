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

class Subject:
	def start(self):
		raise NotImplementedError()

	def stop(self):
		raise NotImplementedError()

	def join(self):
		raise NotImplementedError()

	# Return True if there are not more events to dispatch.
	def eof(self):
		raise NotImplementedError()

	def dispatch(self):
		raise NotImplementedError()

	def peekDateTime(self):
		# Return the datetime for the next event.
		# This is needed to properly synchronize non-realtime subjects.
		raise NotImplementedError()

	def getDispatchPriority(self):
		# Returns a number (or None) used to order subjects within the dispatch queue.
		# The return value should never change.
		return None

# This class is responsible for dispatching events from multiple subjects, synchronizing them if necessary.
class Dispatcher:
	def __init__(self):
		self.__subjects = []
		self.__stopped = False

	def stop(self):
		self.__stopped = True

	def getSubjects(self):
		return self.__subjects

	def addSubject(self, subject):
		if subject.getDispatchPriority() == None:
			self.__subjects.append(subject)
		else:
			# Find the position for the subject's priority.
			pos = 0
			for s in self.__subjects:
				if s.getDispatchPriority() == None or subject.getDispatchPriority() < s.getDispatchPriority():
					break
				pos += 1
			self.__subjects.insert(pos, subject)

	def __dispatch(self):
		smallestDateTime = None
		toDispatch = []
		ret = False

		# Scan for the lowest datetime, dispaching on realtime subjects as the appear.
		for subject in self.__subjects:
			if not subject.eof():
				ret = True
				nextDateTime = subject.peekDateTime()
				if nextDateTime == None:
					subject.dispatch()
				elif smallestDateTime == None:
					assert(len(toDispatch) == 0)
					smallestDateTime = nextDateTime
					toDispatch.append(subject)
				elif nextDateTime == smallestDateTime:
					toDispatch.append(subject)
				elif nextDateTime < smallestDateTime:
					smallestDateTime = nextDateTime
					toDispatch = [subject]

		# Dispatch on those subjects with the smallest datetime.
		for subject in toDispatch:
			subject.dispatch()
		return ret

	def run(self):
		try:
			for subject in self.__subjects:
				subject.start()

			while not self.__stopped and self.__dispatch():
				pass
		finally:
			for subject in self.__subjects:
				subject.stop()
			for subject in self.__subjects:
				subject.join()

