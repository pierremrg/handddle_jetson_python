import threading
import time
import io
import json
import random
import requests
from datetime import datetime
from lib.influxdb_service import InfluxdbService

from messages.tlv_message import TLVMessage
from messages.tlv_data import TLVData
from messages.message import *

import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = "/var/log/handddle_python_logging/datas/datas.log"
FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")

file_logger = logging.getLogger('datas')
file_logger.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=7)
file_handler.setFormatter(FORMATTER)

file_logger.addHandler(file_handler)
file_logger.propagate = False

######################
# Read received data #
######################

class ReadDataThread(threading.Thread):
	def __init__(self, se, api_server_config, influxdb_config, uids, transfer_queue, status_dict, last_data, debug):
		threading.Thread.__init__(self)
		self.se = se
		self.api_server_config = api_server_config
		self.influxdb_config = influxdb_config
		self.uids = uids
		self.transfer_queue = transfer_queue
		self.status_dict = status_dict
		self.last_data = last_data
		self.debug = debug
		self.influxdb_service = InfluxdbService(influxdb_config, debug)

	def run(self):

		file_logger.info('Started ReadDataThread')
		time.sleep(0.5)

		while True:  # Infinite loop

			try:

				time.sleep(2)
				has_data_to_send = False
				data_to_send = {}

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
						# raw_received_data = '01010010C0C0C0C0020C000200FF000000000000FF' # Weight
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
								for tlv_data in tlv_message.payload:
									message = tlv_data.payload

									if type(message) is MainMessage:
										has_data_to_send = True

										# Shift system code if needed
										if 'shift' in MainMessage.DATA_TYPES[message.subtype]:
											shift = MainMessage.DATA_TYPES[message.subtype]['shift']

											if shift == 1:
												system_code = system_code.replace('R', 'B').replace('T', 'R')
											elif shift == -1:
												system_code = system_code.replace('R', 'T').replace('B', 'R')

										if system_code not in data_to_send:
											data_to_send[system_code] = {}
										data_to_send[system_code][message.data.getKey()] = message.data.getValue()

										file_logger.info('<<< Message received on port ' + port_name + ': ' + str(message))

										self.status_dict[tlv_message.uid] = {
											'system_code': system_code, 'check_date': datetime.now(), 'port': port_name
										}

										# Save last data
										if system_code not in self.last_data:
											self.last_data[system_code] = {}
										self.last_data[system_code][message.data.getKey()] = message.data.getValue()

									if type(message) is CommandMessage:
										self.transfer_queue.put(tlv_message.hex_data)


							except requests.exceptions.ConnectionError as e:
								file_logger.error('The application is not connected to internet. No data sent.')

							except requests.exceptions.ReadTimeout as e:
								file_logger.error('The application could not reach the web server. No data sent.\nDetails:', e)

							except Exception as e:
								file_logger.error('Error with a message received on port {}: {} (Raw message: {})'.format(port_name, e, chunk.hex()))

				# Send all data to influxdb
				if has_data_to_send:
					self.influxdb_service.writeDataBySystemCode(data_to_send)

			except Exception as e:
				file_logger.error('ERROR: An error occured while dealing with received data.')
				file_logger.error(str(e))
