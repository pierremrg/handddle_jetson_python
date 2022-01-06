import threading
import os
from os import path as osp
import re
import json
import time
import io
import glob

from messages.tlv_message import TLVMessage
from messages.tlv_data import TLVData

################################
# Read received commands files #
################################

class SendCommandsThread(threading.Thread):
	def __init__(self, se, commands_dir, uids, debug, watchdog_interval):
		threading.Thread.__init__(self)
		self.se = se
		self.commands_dir = commands_dir
		self.uids = uids
		self.debug = debug
		self.messages_to_send = []
		self.watchdog_interval = watchdog_interval
		self.watchdog_count = 0

	def run(self):

		print('Started SendCommandsThread')

		try:

			while True:  # Infinite loop

				# print('Reading commands files...')

				# Messages ready to be sent to all STM32
				self.messages_to_send = []

				# Watchdog update
				if self.watchdog_count % self.watchdog_interval == 0:
					message, hexa = TLVMessage.createTLVCommandFromJson(
						'CFFFFFFF', 'update_watchdog', 1
					)

					self.watchdog_count = 0
					self.messages_to_send.append(message)

				# Regular commands
				commands_filenames = [f for f in os.listdir(self.commands_dir) if osp.isfile(osp.join(self.commands_dir, f))]
				commands_filenames = sorted(commands_filenames, key=lambda filename: int(filename.split('.')[0]))

				for commands_filename in commands_filenames:

					with open(osp.join(self.commands_dir, commands_filename), 'r') as commands_file:

						try:
							commands_data = commands_file.read()
							commands_data = re.sub('\s+', '', commands_data)
							commands_data = json.loads(commands_data)

							# Here (= no error), we have a JSON document
							commands_data = commands_data['commands']

							for system_code, commands_data in commands_data.items():
								if system_code in self.uids.values():
									for _uid in self.uids:
										if system_code == self.uids[_uid]:
											uid = _uid

									for command_name, command_value in commands_data.items():
										message, hexa = TLVMessage.createTLVCommandFromJson(
											uid, command_name, command_value
										)

										self.messages_to_send.append(message)

										# Test - Uncomment this line to check if the message is well formated
										# print(TLVMessage(io.BytesIO(message)))

								else:
									raise Exception('Unknown system code ({}).'.format(system_code))

						except Exception as e:
							print('Error:', e)


				# Actually send messages
				self.sendMessages()


				# Remove commands files
				for f in glob.glob(osp.join(self.commands_dir, '*')):
					os.remove(f)

				self.watchdog_count += 1
				time.sleep(1)

		except Exception as e:
			print('ERROR: An error occured while sending commands.')
			# raise e

		finally:
			for port_name in self.se:
				try:
					self.se[port_name].close()
				except Exception as e:
					print('Cannot close port {}: {}'.format(port_name, e))


	def sendMessages(self):

		for message in self.messages_to_send:

			if not self.debug:

				# Send the message to all connected STM32
				for port_name in self.se:
					for i in range(len(message)):
						self.se[port_name].write(message[i:i + 1])
						time.sleep(0.001)

			print('>>> Sent command: {:040x}'.format(int.from_bytes(message, byteorder='big')))
