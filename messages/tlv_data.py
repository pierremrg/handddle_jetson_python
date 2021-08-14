

class TLVData:

	HEADER_LENGTH = 4

	MESSAGE_TYPES = {
		'INTERNAL': 0,
		'COMMAND': 1,
		'MAIN': 2,
		'SECONDARY': 3,
		'ERROR': 4,
		'INFORMATION': 5
	}

	def __init__(self):
		self.type = None
		self.subtype = None
		self.length = None
		self.payload = None


	def setPayload(self, payload):
		self.payload = payload


	def __str__(self):
		content = '[TLV Data | Type: {}/{} - Length: {} - Payload: {}]'.format(
			self.type, self.subtype, self.length,
			self.payload.hex() if type(self.payload) is bytes else str(self.payload)
		)

		return content

	def __repr__(self):
		return self.__str__()