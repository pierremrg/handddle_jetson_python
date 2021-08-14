import threading
import time
import io
import json
from os import path as osp
import random

from messages.tlv_message import TLVMessage
from messages.tlv_data import TLVData
from messages.message import *

######################
# Read received json_files #
######################

class ReadDataThread(threading.Thread):
	def __init__(self, se, received_data_dir, uids, debug):
		threading.Thread.__init__(self)
		self.se = se
		self.received_data_dir = received_data_dir
		self.uids = uids
		self.debug = debug

	def run(self):

		print('Started ReadDataThread')
		time.sleep(0.5)

		try:

			while True:  # Infinite loop

				for port_name in self.se:

					has_data = False
					raw_received_data = None

					if self.se[port_name] and self.se[port_name].in_waiting:
						raw_received_data = self.se[port_name].readline()
						has_data = True

					if self.debug:
						raw_received_data = input('Enter a valid hex message received from the STM32: ')

						# Example test messages
						raw_received_data = '01010010C0C0C0C002010001AA02020002FEFE00' # Main / Temp + Hum
						# raw_received_data = '01010010C0C0C0C0000500010102020002FEFE00' # Internal
						# raw_received_data = '01010010C0C0C0C0010400010400000000000000' # Command
						# raw_received_data = '01010010C0C0C0C0030300021001050200010000' # Other
						# raw_received_data = '01010010C0C0C0C0040100010100000000000000' # Error

						if raw_received_data != '':
							raw_received_data = bytes.fromhex(raw_received_data)
							has_data = True

					if has_data:

						try:
							# TODO Check if the following line gets binary data from the STM32 correctly
							message_stream = io.BytesIO(raw_received_data)
							tlv_message = TLVMessage(message_stream)

							# Here (= no error), we have a valid message from the STM32
							if tlv_message.uid in self.uids:
								system_code = self.uids[tlv_message.uid]
							else:
								raise Exception('Unknown UID ({}).'.format(tlv_message.uid))

							# Receiving json_files
							for tlv_data in tlv_message.payload:
								current_timestamp = time.time() + random.random() / 1000
								message = tlv_data.payload

								print('<<< Message received on port ' + port_name + ': ' + str(message))

								if type(message) is MainMessage:
									with open(osp.join(self.received_data_dir, str(current_timestamp) + '.json'), 'w') as received_data_file:
										json_data = {'received_data': {system_code: {}}}
										json_data['received_data'][system_code][message.data_name] = message.data_value

										# Write received json_files to file
										json.dump(json_data, received_data_file)


						except Exception as e:
							print('Error with a message received on port {}: {} (Raw message: {})'.format(port_name, e, raw_received_data.hex()))

				time.sleep(0.5)


		except Exception as e:
			print('ERROR: An error occured while reading json_files.')
			raise e

		finally:
			for system_code in self.se:
				self.se[system_code].close()