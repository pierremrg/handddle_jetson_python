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

################################
# Read received commands files #
################################

class SendCommandsThread(threading.Thread):
	def __init__(self, se, api_server_config, uids, transfer_queue, debug, watchdog_interval):
		threading.Thread.__init__(self)
		self.se = se
		self.api_server_config = api_server_config
		self.uids = uids
		self.transfer_queue = transfer_queue
		self.debug = debug
		self.messages_to_send = []
		self.watchdog_interval = watchdog_interval
		self.watchdog_count = 0

		self.last_check_date = int(time.time())
		self.is_connected = True

	def run(self):

		print('Started SendCommandsThread')

		while True:  # Infinite loop
			try:
				waiting_duration = 2 if self.is_connected else 8

				self.watchdog_count += waiting_duration
				time.sleep(waiting_duration)

				# Messages ready to be sent to all STM32
				self.messages_to_send = []

				# Watchdog update
				# TODO Create another thread for the watchdog
				if self.watchdog_count >= self.watchdog_interval:
					message, hexa = TLVMessage.createTLVCommandFromJson(
						'CFFFFFFF', 'update_watchdog', 1
					)

					self.watchdog_count = 0
					self.messages_to_send.append(message)

				# Regular commands
				r = self.api_server_config['session'].get(
					url=self.api_server_config['protocol'] + '://' + self.api_server_config['host'] + '/public/api/farm_commands',
					params={
						'organization_group.code': self.api_server_config['licence_key'],
						'sent_date[gte]': self.last_check_date
					},
					timeout=10
				)
				self.is_connected = True
				commands_list = r.json()
				print(commands_list)
				self.last_check_date = int(time.time())

				for command in commands_list:
					try:
						if command['system_code'] in self.uids.values():
							for uid in self.uids:
								if command['system_code'] == self.uids[uid]:
									message, hexa = TLVMessage.createTLVCommandFromJson(uid, command['action'], int(command['data']))
									self.messages_to_send.append(message)

									# Test - Uncomment this line to check if the message is well formated
									# print(TLVMessage(io.BytesIO(message)))

						else:
							raise Exception('Unknown system code ({}).'.format(command['system_code']))

					except Exception as e:
						print('Error:', e)

				# Add transfered commands
				while not self.transfer_queue.empty():
					self.messages_to_send.append(self.transfer_queue.get())

				# Actually send messages
				self.sendMessages()

			except requests.exceptions.ConnectionError as e:
				self.is_connected = False
				print('The application is not connected to internet. Retrying...')

			except requests.exceptions.ReadTimeout as e:
				self.is_connected = False
				print('The application could not reach the web server. Retrying...\nDetails:', e)

			except Exception as e:
				print('ERROR: An error occured while sending commands.')


	def sendMessages(self):

		for message in self.messages_to_send:

			if not self.debug:

				# Send the message to all connected STM32
				for port_name in self.se:
					for i in range(len(message)):
						self.se[port_name].write(message[i:i + 1])
						time.sleep(0.001)

			print('>>> Sent command: {:040x}'.format(int.from_bytes(message, byteorder='big')))
