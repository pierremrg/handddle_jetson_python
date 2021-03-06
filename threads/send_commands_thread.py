import threading
import os
from os import path as osp
import re
import json
import time
import io
import glob
import requests

from messages.tlv_message import TLVMessage
from messages.tlv_data import TLVData

import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = "/var/log/handddle_python_logging/commands/commands.log"
FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")

file_logger = logging.getLogger('commands')
file_logger.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=7)
file_handler.setFormatter(FORMATTER)

file_logger.addHandler(file_handler)
file_logger.propagate = False

################################
# Read received commands files #
################################

class SendCommandsThread(threading.Thread):
	def __init__(self, se, api_server_config, uids, transfer_queue, debug):
		threading.Thread.__init__(self)
		self.se = se
		self.api_server_config = api_server_config
		self.uids = uids
		self.transfer_queue = transfer_queue
		self.debug = debug
		self.messages_to_send = []

		self.last_check_date = int(time.time())
		self.is_connected = True

	def run(self):

		file_logger.info('Started SendCommandsThread')

		while True:  # Infinite loop
			try:
				waiting_duration = 2 if self.is_connected else 8
				time.sleep(waiting_duration)

				# Messages ready to be sent to all STM32
				self.messages_to_send = []

				# Regular commands
				r = self.api_server_config['session'].get(
					url=self.api_server_config['protocol'] + '://' + self.api_server_config['host'] + '/public/api/farm_commands',
					params={
						'organization_group.code': self.api_server_config['licence_key'],
						'sent_date[gte]': self.last_check_date
					},
					timeout=10
				)
				commands_list = r.json()

				self.is_connected = True
				self.last_check_date = int(time.time())

				for command in commands_list:
					try:
						if command['system_code'] in self.uids.values():
							for uid in self.uids:
								if command['system_code'] == self.uids[uid]:
									message, hexa = TLVMessage.createTLVCommandFromJson(uid, command['action'], int(command['data']))
									self.messages_to_send.append(message)

									# Test - Uncomment this line to check if the message is well formated
									# file_logger.info(TLVMessage(io.BytesIO(message)))

						else:
							raise Exception('Unknown system code ({}).'.format(command['system_code']))

					except Exception as e:
						file_logger.error('Error:', e)

				# Add transfered commands
				while not self.transfer_queue.empty():
					self.messages_to_send.append(self.transfer_queue.get())

				# Actually send messages
				self.sendMessages()

			except requests.exceptions.ConnectionError as e:
				self.is_connected = False
				file_logger.error('The application is not connected to internet. Retrying...')

			except requests.exceptions.ReadTimeout as e:
				self.is_connected = False
				file_logger.error('The application could not reach the web server. Retrying...\nDetails:', e)

			except Exception as e:
				file_logger.error('ERROR: An error occured while sending commands.')


	def sendMessages(self):

		for message in self.messages_to_send:

			if not self.debug:

				# Send the message to all connected STM32
				for port_name in self.se:
					for i in range(len(message)):
						self.se[port_name].write(message[i:i + 1])
						time.sleep(0.001)

			file_logger.info('>>> Sent command: {:040x}'.format(int.from_bytes(message, byteorder='big')))
