import io
from importlib import import_module

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
		2: {'name': 'door_closed', 'values': [0, 1]},
		3: {'name': 'forcing_door', 'values': [1]},
		4: {'name': 'temperature', 'values': [t for t in range(100+1)]},
		5: {'name': 'led_color', 'values': [0, 1, 2, 3, 4, 5, 6, 7, 8]},
		6: {'name': 'printing_state', 'values': [0, 1, 2, 3, 4, 5, 6, 7]},
		7: {'name': 'air_extraction', 'values': [e for e in range(100+1)]},
		8: {'name': 'relay_off', 'values': [0, 1]},
		9: {'name': 'tare', 'values': [1]},
		10: {'name': 'get_weight', 'values': [1]},
		11: {'name': 'update_watchdog', 'values': [1]},
		12: {'name': 'force_reset', 'values': [1]},
		13: {'name': 'buzzer', 'values': [0,1]}
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
		1: {'name': 'temperature', 'class': 'temperature_data_persister'},
		2: {'name': 'humidity', 'class': 'default_data_persister'},
		3: {'name': 'temperature_humidity', 'class': 'default_data_persister'}, # Unused
		4: {'name': 'current_ee', 'class': 'default_data_persister'},
		5: {'name': 'current_printer', 'class': 'default_data_persister'},
		6: {'name': 'door_closed', 'class': 'door_closed_data_persister'},
		7: {'name': 'pollution', 'class': 'default_data_persister'}, # Unused
		8: {'name': 'sound', 'class': 'default_data_persister'}, # Unused
		9: {'name': 'led_color', 'class': 'default_data_persister'},
		10: {'name': 'printing_state', 'class': 'default_data_persister'}, # Unused
		11: {'name': 'latch_status', 'class': 'default_data_persister'}, # Unused
		12: {'name': 'weight', 'class': 'default_data_persister'},
		13: {'name': 'pm1', 'class': 'default_data_persister'},
		14: {'name': 'pm25', 'class': 'default_data_persister'},
		15: {'name': 'pm10', 'class': 'default_data_persister'},
		16: {'name': 'CO2', 'class': 'default_data_persister'}, # Unused
		17: {'name': 'TVOC', 'class': 'default_data_persister'}, # Unused
		18: {'name': 'TVOC_Warning', 'class': 'default_data_persister'}, # Unused
		19: {'name': 'CO2_warning', 'class': 'default_data_persister'}, # Unused
		20: {'name': 'Typology', 'class': 'default_data_persister'} # Unused
	}

	def __init__(self, subtype, content):
		super().__init__(subtype, content)

		if self.subtype not in MainMessage.DATA_TYPES.keys():
			raise Exception('Invalid main message type: {}'.format(self.subtype))

		data_class = getattr(import_module('data_persisters.' + MainMessage.DATA_TYPES[self.subtype]['class']),
			''.join(x for x in MainMessage.DATA_TYPES[self.subtype]['class'].title() if x.isalnum())
		)
		self.data = data_class(
			MainMessage.DATA_TYPES[self.subtype]['name'],
			int.from_bytes(self.stream.read(), byteorder='big')
		)

	def __repr__(self):
		return '[Main message | Data name: {} | Data value: {}]'.format(self.data.getKey(), self.data.getValue())


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

