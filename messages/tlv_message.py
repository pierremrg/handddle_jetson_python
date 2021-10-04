import io
from messages.tlv_data import TLVData
from messages.message import *

class TLVMessage:

	HEADER_LENGTH = 4
	CORRECT_TYPE = 257 # 0x0101

	def __init__(self, stream):
		stream.seek(0)

		self.type = int.from_bytes(stream.read(2), byteorder='big')

		if self.type != TLVMessage.CORRECT_TYPE:
			raise Exception('Incorrect TLVMessage type.')

		self.length = int.from_bytes(stream.read(2), byteorder='big')

		total_length = stream.getbuffer().nbytes

		if self.length != total_length - TLVMessage.HEADER_LENGTH:
			raise Exception('Incorrect TLVMessage length.')

		# UID + Payload
		self.uid = stream.read(4).hex()
		self.payload = TLVMessage.parseTVLMessagePayload(stream.read())


	def __str__(self):
		content = 'TLV Message\n'
		content += '\t- Type: {}\n'.format(self.type)
		content += '\t- Length: {}\n'.format(self.length)
		content += '\t- UID: {}\n'.format(self.uid)
		content += '\t- Payload: {}'.format(' '.join(str(d) for d in self.payload))

		return content


	@staticmethod
	def parseTVLMessagePayload(rawPayload):
		stream = io.BytesIO(rawPayload)
		total_length = stream.getbuffer().nbytes

		data_list = []

		i = 0
		while i < total_length:
			data = TLVData()

			data.type = int.from_bytes(stream.read(1), byteorder='big')

			if data.type not in TLVData.MESSAGE_TYPES.values():
				raise Exception('Incorrect TLVData type: {}'.format(data.type))

			data.subtype = int.from_bytes(stream.read(1), byteorder='big')
			data.length = int.from_bytes(stream.read(2), byteorder='big')
			i += 4

			if data.length == 0:
				break

			if data.length > total_length - i:
				raise Exception('Incorrect TLVData length.')


			# Parse the message depending on the message type
			if data.type == TLVData.MESSAGE_TYPES['INTERNAL']:
				data.payload = InternalMessage(data.subtype, stream.read(data.length))
			elif data.type == TLVData.MESSAGE_TYPES['COMMAND']:
				data.payload = CommandMessage(data.subtype, stream.read(data.length))
			elif data.type == TLVData.MESSAGE_TYPES['MAIN']:
				data.payload = MainMessage(data.subtype, stream.read(data.length))
			elif data.type == TLVData.MESSAGE_TYPES['SECONDARY']:
				data.payload = SecondaryMessage(data.subtype, stream.read(data.length))
			elif data.type == TLVData.MESSAGE_TYPES['ERROR']:
				data.payload = ErrorMessage(data.subtype, stream.read(data.length))
			elif data.type == TLVData.MESSAGE_TYPES['INFORMATION']:
				data.payload = InformationMessage(data.subtype, stream.read(data.length))


			else:
				data.payload = '/!\ Invalid message type (Content: {})'.format(stream.read(data.length).hex())

			i += data.length

			data_list.append(data)

		return data_list

	@staticmethod
	def createTLVCommandFromJson(hex_uid, command_name, command_value):
		hexa  = '{:04x}'.format(TLVMessage.CORRECT_TYPE) # Type
		hexa += '{:04x}'.format(16) # Length
		hexa += str(hex_uid).zfill(8) # UID
		hexa += '{:02x}'.format(TLVData.MESSAGE_TYPES['COMMAND']) # Type = command

		# Get command message id
		command_id = None
		for _command_id, command_type in CommandMessage.COMMAND_TYPES.items():
			if command_type['name'] == command_name:
				command_id = _command_id

		if command_id is None:
			raise Exception('Unsupported command: {}'.format(command_name))

		if command_value not in CommandMessage.COMMAND_TYPES[command_id]['values']:
			raise Exception('Unsupported value for the {} command: {}'.format(
				command_name, command_value
			))

		hexa += '{:02x}'.format(command_id) # Command type

		hexa += '{:04x}'.format(1) # Value length (1 byte)

		hexa += '{:02x}'.format(command_value) # Value

		hexa = hexa.ljust(20*2, '0') # Padding

		return bytes.fromhex(hexa), hexa