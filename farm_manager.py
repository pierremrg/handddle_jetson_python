import serial
import serial.tools.list_ports as port_list
import json
import yaml
import time
import os
from os import path as osp
import re
from collections import defaultdict

from threads.read_data_thread import ReadDataThread
from threads.send_commands_thread import SendCommandsThread

class FarmManager:

	def __init__(self, config_filepath):

		# Configuration
		self.config_filepath = config_filepath
		self.config = None

		self.root_dir = None
		self.received_data_dir = None
		self.commands_dir = None

		self.serial_baudrate = None
		self.serial_ports_prefix = None

		self.uids = {}

		self.debug = False

		self.loadConfiguration()

		# Serial
		self.se = {}
		self.loadUSBPorts()

		# Multithreading
		self.readDataThread = ReadDataThread(self.se, self.received_data_dir, self.uids, self.debug)
		self.sendCommandsThread = SendCommandsThread(self.se, self.commands_dir, self.uids, self.debug)


	def loadConfiguration(self):
		with open(self.config_filepath, 'r') as config_file:
			self.config = yaml.load(config_file, Loader=yaml.FullLoader)

		self.debug = self.config['debug']

		self.root_dir = self.config['root_dir']
		self.received_data_dir = osp.join(self.root_dir, self.config['received_data_dir'])
		self.commands_dir = osp.join(self.root_dir, self.config['commands_dir'])

		if not osp.isdir(self.received_data_dir):
			os.makedirs(self.received_data_dir)

		if not osp.isdir(self.commands_dir):
			os.makedirs(self.commands_dir)

		self.serial_baudrate = self.config['serial']['baudrate']
		self.serial_ports_prefix = self.config['serial']['ports_prefix']

		self.uids = self.config['uids']

	def loadUSBPorts(self):
		print('------------------------------')
		print('Ports initilization:')

		if not self.debug:

			ports = list(port_list.comports())

			self.se = {}
			for p in ports:
				port_full_name = p[0]
				port_name = p[1]

				if port_name.startswith(self.serial_ports_prefix):
					self.se[port_name] = serial.Serial()
					self.se[port_name].baudrate = self.serial_baudrate
					self.se[port_name].port = port_full_name
					self.se[port_name].open()

					time.sleep(0.1)
					self.se[port].flushInput()
					self.se[port].flushOutput()

					print('\t- Port {} initialized.'.format(port))

		else:
			self.se['P0'] = None
			print('\t- Port P0 initialized [DEBUG].')

		print('{} port(s) initialized.'.format(len(self.se)))
		print('------------------------------')


	def startProcesses(self):

		if self.readDataThread is not None:
			self.readDataThread.start()

		if self.sendCommandsThread is not None:
			self.sendCommandsThread.start()


if __name__ == '__main__':

	farmManager = FarmManager('config.yaml')

	farmManager.startProcesses()
