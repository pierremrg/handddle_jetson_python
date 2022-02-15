import threading
import time
import io
import json
import random

from messages.tlv_message import TLVMessage
from messages.tlv_data import TLVData
from messages.message import *

######################
# Read received data #
######################

class ReadDataThread(threading.Thread):
	def __init__(self, se, api_server_config, uids, transfer_queue, debug):
		threading.Thread.__init__(self)
		self.se = se
		self.api_server_config = api_server_config
		self.uids = uids
		self.transfer_queue = transfer_queue
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

						raw_received_data = b''
						while self.se[port_name].in_waiting:
							raw_received_data += self.se[port_name].read(1)
							time.sleep(0.001)

						has_data = True

					if self.debug:
						raw_received_data = input('Enter a valid hex message received from the STM32: ')

						# Example test messages
						# raw_received_data = ''
						# raw_received_data = '01010010C0C0C0C002010001AA00000000000000FF' # Main / Temp
						# raw_received_data = '01010010C0C0C0C002010001AA00000000000000FF' # Main / Hum
						# raw_received_data = '01010010C0C0C0C002010001AA02020002FEFE00FF' # Main / Temp + Hum
						# raw_received_data = '01010010C0C0C0C0000500010102020002FEFE00FF' # Internal
						# raw_received_data = '01010010C0C0C0C0010400010400000000000000FF' # Command
						# raw_received_data = '01010010C0C0C0C0030300021001050200010000FF' # Other
						# raw_received_data = '01010010C0C0C0C0040100010100000000000000FF' # Error

						if raw_received_data != '':
							raw_received_data = bytes.fromhex(raw_received_data)
							has_data = True

					if has_data:

						raw_received_data_chunks = [raw_received_data[i:i+21] for i in range(0, len(raw_received_data), 21)]

						for chunk in raw_received_data_chunks:
							chunk = chunk[:-1]		
							if len(chunk) == 0:
								continue			

							try:
								# TODO Check if the following line gets binary data from the STM32 correctly
								tlv_message = TLVMessage(chunk)

								# Here (= no error), we have a valid message from the STM32
								if tlv_message.uid in self.uids:
									system_code = self.uids[tlv_message.uid]
								else:
									raise Exception('Unknown UID ({}).'.format(tlv_message.uid))

								# Manage received data
								data_to_send = {} # Data to send for one specific system code
								has_data_to_send = False
								for tlv_data in tlv_message.payload:
									message = tlv_data.payload

									if type(message) is MainMessage:
										has_data_to_send = True
										data_to_send[message.data.getKey()] = message.data.getValue()
										print('<<< Message received on port ' + port_name + ': ' + str(message))

									if type(message) is CommandMessage:
										self.transfer_queue.put(tlv_message.hex_data)

								# Actually send data
								if has_data_to_send:
									self.api_server_config['session'].post(
										url=self.api_server_config['protocol'] + '://' + self.api_server_config['host'] + '/public/api/farm_datas',
										headers={
											'Content-type': 'application/json'
										},
										data=json.dumps({
											'system_code': system_code,
											'measure_date': int(time.time()),
											'data': data_to_send
										})
									)

							except Exception as e:
								print('Error with a message received on port {}: {} (Raw message: {})'.format(port_name, e, chunk.hex()))

				time.sleep(0.1)


		except Exception as e:
			print('ERROR: An error occured while dealing with received data.')
			raise e

		finally:
			for system_code in self.se:
				self.se[system_code].close()
