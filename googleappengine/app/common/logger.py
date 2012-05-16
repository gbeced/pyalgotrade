import logging

class Logger:
	def __init__(self, maxErrors = 20):
		self.__maxErrors = maxErrors 

	def info(self, msg):
		logging.info(msg)

	def error(self, msg):
		if self.__maxErrors > 0:
			self.__maxErrors -= 1
			logging.error(msg)

logging.getLogger().setLevel(logging.DEBUG)
