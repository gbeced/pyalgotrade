# PyAlgoTrade
# 
# Copyright 2013 Gabriel Martin Becedillas Ruiz
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

import Queue
import threading
import json
import types

from pyalgotrade import observer
import pyalgotrade.logger

import tweepy
from tweepy import streaming

logger = pyalgotrade.logger.getLogger("twitter")

# This listener just pushs data into a queue.
class Listener(streaming.StreamListener):
	def __init__(self, queue):
		streaming.StreamListener.__init__(self)
		self.__queue = queue

	def on_connect(self):
		logger.info("Connected.")

	def on_timeout(self):
		logger.error("Timeout.")

	def on_data(self, data):
		self.__queue.put(data)
		return True

	def on_error(self, status):
		logger.error(status)
		return False

# https://dev.twitter.com/docs/streaming-apis/parameters
class TwitterFeed(observer.Subject):
	"""Class responsible for connecting to Twitter's public stream API and dispatching events.
	Check https://dev.twitter.com/docs/streaming-apis/streams/public for more information.

	:param consumerKey: Consumer key.
	:type consumerKey: string.
	:param consumerSecret: Consumer secret.
	:type consumerSecret: string.
	:param accessToken: Access token.
	:type accessToken: string.
	:param accessTokenSecret: Access token secret.
	:type accessTokenSecret: string.
	:param track: A list of phrases which will be used to determine what Tweets will be delivered
		on the stream. A phrase may be one or more terms separated by spaces, and a phrase will match
		if all of the terms in the phrase are present in the Tweet, regardless of order and ignoring case.
	:type track: list.
	:param follow: A list of user IDs, indicating the users whose Tweets should be delivered on the
		stream. Following protected users is not supported.
	:type follow: list.
	:param languages: A list of language IDs a defined in http://tools.ietf.org/html/bcp47.
	:type languages: list.

	.. note::
		* Go to http://dev.twitter.com and create an app. The consumer key and secret will be generated for you after that.
		* Create an access token under the "Your access token" section.
		* At least **track** or **follow** have to be set.
	"""

	QUEUE_TIMEOUT = 0.01
	MAX_EVENTS_PER_DISPATCH = 50

	def __init__(self, consumerKey, consumerSecret, accessToken, accessTokenSecret, track=[], follow=[], languages=[]):
		if type(track) != types.ListType:
			raise Exception("track must be a list")
		if type(follow) != types.ListType:
			raise Exception("follow must be a list")
		if type(languages) != types.ListType:
			raise Exception("languages must be a list")

		self.__event = observer.Event()
		self.__queue = Queue.Queue()
		self.__thread = None
		self.__running = False

		listener = Listener(self.__queue)
		auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
		auth.set_access_token(accessToken, accessTokenSecret)
		self.__stream = tweepy.Stream(auth, listener)
		self.__track = track
		self.__follow = follow
		self.__languages = languages

	def __threadMain(self):
		try:
			logger.info("Initializing Twitter client.")
			self.__stream.filter(track=self.__track, follow=self.__follow, languages=self.__languages)
		finally:
			logger.info("Twitter client finished.")
			self.__running = False
	
	def __dispatchImpl(self):
		ret = False
		try:
			nextTweet = json.loads(self.__queue.get(True, TwitterFeed.QUEUE_TIMEOUT))
			ret = True
			self.__event.emit(nextTweet)
		except Queue.Empty:
			pass
		return ret

	def subscribe(self, callback):
		"""Subscribe to Twitter events. The event handler will receive a dictionary with the data as defined in:
		https://dev.twitter.com/docs/streaming-apis/messages#Public_stream_messages.
		"""
		return self.__event.subscribe(callback)

	def start(self):
		if self.__thread != None:
			raise Exception("Already running")

		# Start the thread that will run the client.
		self.__thread = threading.Thread(target=self.__threadMain)
		self.__thread.start()
		self.__running = True

	def stop(self):
		try:
			if self.__thread != None and self.__thread.is_alive():
				logger.info("Shutting down Twitter client.")
				self.__stream.disconnect()
		except Exception, e:
			logger.error("Error disconnecting stream: %s." % (str(e)))

	def join(self):
		if self.__thread != None:
			self.__thread.join()
		assert(self.__running == False)

	def eof(self):
		return not self.__running

	def dispatch(self):
		dispatched = TwitterFeed.MAX_EVENTS_PER_DISPATCH
		while self.__dispatchImpl() and dispatched > 0:
			dispatched -= 1

	def peekDateTime(self):
		return None

	def getDispatchPriority(self):
		return None

