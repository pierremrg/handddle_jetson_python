from data_persisters.data_persister import DataPersister

class DoorClosedDataPersister(DataPersister):

	def __init__(self, key, value):
		super().__init__(key, value)

		self.last_value = -1
		self.last_insert_date = int(time.time())

	def shouldBePersisted(self):
		now = int(time.time())

		if self.value != self.last_value or self.last_insert_date < now - 10:
			self.last_value = self.value
			self.last_insert_date = now
			return True

		return False