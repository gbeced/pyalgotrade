import cgi

class Form:
	def __init__(self, request, fieldNames):
		self.__values = {}
		for name in fieldNames:
			self.__values[name] = request.get(name)

	def setRawValue(self, name, value):
		self.__values[name] = value

	def getRawValue(self, name):
		return self.__values[name]

	def getSafeValue(self, name):
		ret = self.getRawValue(name)
		if ret != None:
			ret = cgi.escape(ret)
		return ret

	def getValuesForTemplate(self):
		ret = {}
		for name in self.__values.keys():
			ret[name] = self.getSafeValue(name)
		return ret

