from abc import ABC, abstractmethod

class DataPersister(ABC):

	def __init__(self, key, value):
		self.key = key
		self.value = value

	def getKey(self):
		return self.key

	def getValue(self):
		return self.value

	def shouldBePersisted(self):
		return True