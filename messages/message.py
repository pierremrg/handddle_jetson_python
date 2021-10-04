import io

class Message:

	def __init__(self, subtype, content):

		self.subtype = subtype
		self.stream = io.BytesIO(content)


class InternalMessage(Message):

	INTERNAL_TYPES = {
		0: 'ack_general',
		1: 'ack_command',
		5: 'ack_information'
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in InternalMessage.INTERNAL_TYPES.keys():
			raise Exception('Invalid internal message type: {}'.format(self.subtype))

		self.information_type = InternalMessage.INTERNAL_TYPES[self.subtype]
		self.infomation_value = int.from_bytes(self.stream.read(), byteorder='big')

	def __repr__(self):
		return '[Internal message | Information type: {} | Information value: {}]'.format(
			self.information_type, self.infomation_value
		)


class CommandMessage(Message):

	COMMAND_TYPES = {
		0: {'name': 'ack', 'values': [0, 1]},
		1: {'name': 'on_off', 'values': [0, 1]},
		2: {'name': 'door_open', 'values': [0, 1]},
		3: {'name': 'forcing_door', 'values': [1]},
		4: {'name': 'temperature', 'values': [t for t in range(100)]},
		5: {'name': 'led_color', 'values': [0, 1, 2, 3, 4, 5, 6, 7]},
		6: {'name': 'printing_state', 'values': [0, 1, 2, 3, 4, 5, 6, 7]},
		7: {'name': 'air_extraction', 'values': [e for e in range(100)]},
		8: {'name': 'relay', 'values': [1]}
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in CommandMessage.COMMAND_TYPES.keys():
			raise Exception('Invalid command message type: {}'.format(self.subtype))

		self.command_name = CommandMessage.COMMAND_TYPES[self.subtype]['name']
		self.command_value = int.from_bytes(self.stream.read(), byteorder='big')

		if self.command_value not in CommandMessage.COMMAND_TYPES[self.subtype]['values']:
			raise Exception('Invalid command message "{}" with value "{}"'.format(
				self.command_name, self.command_value
			))


	def __repr__(self):
		return '[Command message | Command name: {} | Command value: {}]'.format(self.command_name, self.command_value)



class MainMessage(Message):

	DATA_TYPES = {
		1: 'temperature',
		2: 'humidity',
		3: 'temperature_humidity',
		4: 'current_ee',
		5: 'current_printer',
		6: 'door_state',
		7: 'pollution',
		8: 'sound',
		9: 'led_color',
		10: 'printing_state'
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in MainMessage.DATA_TYPES.keys():
			raise Exception('Invalid main message type: {}'.format(self.subtype))

		self.data_name = MainMessage.DATA_TYPES[self.subtype]
		self.data_value = int.from_bytes(self.stream.read(), byteorder='big')

	def __repr__(self):
		return '[Main message | Data name: {} | Data value: {}]'.format(self.data_name, self.data_value)


class SecondaryMessage(Message):

	DATA_TYPES = {
		1: 'tachy_extraction',
		2: 'tachy_heating',
		3: 'rack_temperature',
		4: 'heating_temperature',
		5: 'pressure',
		6: 'relay_state',
		7: 'buzzer_state',
        8: 'preheat_over'
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in SecondaryMessage.DATA_TYPES.keys():
			raise Exception('Invalid secondary message type: {}'.format(self.subtype))

		self.data_name = SecondaryMessage.DATA_TYPES[self.subtype]
		self.data_value = int.from_bytes(self.stream.read(), byteorder='big')

	def __repr__(self):
		return '[Secondary message | Data name: {} | Data value: {}]'.format(self.data_name, self.data_value)


class ErrorMessage(Message):

	DATA_TYPES = {
		1: 'tachy_extraction',
		2: 'heater',
		3: 'environment_temperature',
		4: 'environment_humidity',
		5: 'heater_warning',
		6: 'rack_warning'
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in ErrorMessage.DATA_TYPES.keys():
			raise Exception('Invalid error message type: {}'.format(self.subtype))

		self.data_name = ErrorMessage.DATA_TYPES[self.subtype]

	def __repr__(self):
		return '[Error message | Data name: {}]'.format(self.data_name)



class InformationMessage(Message):

	DATA_TYPES = {
		0: 'ack',
		1: 'day_night',
		2: 'temperature_manual_mode',
		3: 'filtration_manual_mode',
		4: 'pollution_threshold',
		5: 'door_state'
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in InformationMessage.DATA_TYPES.keys():
			raise Exception('Invalid information message type: {}'.format(self.subtype))

		self.data_name = InformationMessage.DATA_TYPES[self.subtype]
		self.data_value = int.from_bytes(self.stream.read(), byteorder='big')

	def __repr__(self):
		return '[Information message | Data name: {} | Data value: {}]'.format(self.data_name, self.data_value)

