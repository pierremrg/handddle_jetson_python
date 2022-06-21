import requests
import serial
import serial.tools.list_ports as port_list
import json
import yaml
import time
import os
from os import path as osp
import re
from collections import defaultdict
from queue import Queue

from threads.read_data_thread import ReadDataThread
from threads.send_commands_thread import SendCommandsThread
from threads.watchdog_thread import WatchdogThread
from threads.scanner_thread import ScannerThread
from threads.gui_thread import GUIThread
from threads.demo_thread import DemoThread

class FarmManager:

	def __init__(self, config_filepath):

		# Configuration
		self.config_filepath = config_filepath
		self.config = None

		self.api_server_config = None
		self.influxdb_config = None

		self.serial_baudrate = None
		self.serial_ports_prefix = None

		self.uids = {}
		self.scanner_config = None
		self.watchdog_interval = None

		self.debug = False
		self.demo = False
		self.display_data = False

		self.loadConfiguration()

		# Serial
		self.se = {}
		self.loadUSBPorts()

		# Command transfer
		self.transfer_queue = Queue(maxsize=100)

		# Status & last data
		self.status_dict = {}
		self.last_data = {}

		# Multithreading
		self.readDataThread = ReadDataThread(self.se, self.api_server_config, self.influxdb_config, self.uids, self.transfer_queue, self.status_dict, self.last_data, self.debug)
		self.sendCommandsThread = SendCommandsThread(self.se, self.api_server_config, self.uids, self.transfer_queue, self.debug)
		self.watchdogThread = WatchdogThread(self.watchdog_interval, self.transfer_queue, self.uids, self.debug)
		self.scannerThread = ScannerThread(self.scanner_config, self.api_server_config, self.debug)
		self.guiThread = GUIThread(self.uids, self.api_server_config, self.status_dict, self.last_data, self.display_data, self.transfer_queue, self.debug)

		self.threads = [
			self.readDataThread,
			self.sendCommandsThread,
			self.watchdogThread,
			self.scannerThread,
			self.guiThread
		]

		if self.demo:
			self.demoThread = DemoThread(self.transfer_queue, self.uids, self.debug)
			self.threads.append(self.demoThread)

	def loadConfiguration(self):
		with open(self.config_filepath, 'r') as config_file:
			self.config = yaml.load(config_file, Loader=yaml.FullLoader)

		self.debug = self.config['debug']
		self.demo = self.config['demo']
		self.display_data = self.config['display_data']

		self.api_server_config = self.config['api_server']
		# Create a unique server session for the whole app
		self.api_server_config['session'] = requests.Session()

		self.influxdb_config = self.config['influxdb']

		# STM communication
		self.serial_baudrate = self.config['serial']['baudrate']
		self.serial_ports_prefix = self.config['serial']['ports_prefix']

		self.uids = self.config['uids']

		self.scanner_config = self.config['scanner']

		self.watchdog_interval = self.config['watchdog_interval']


	def loadUSBPorts(self):
		print('------------------------------')
		print('Ports initilization:')

		if not self.debug:

			ports = list(port_list.comports())

			self.se = {}
			for port_full_name, description, hwid in ports:
				# Do not use the scanner
				hwid = hwid.split()
				
				if len(hwid) > 2 and hwid[2].startswith('SER='):
					usb_serial_number = int(hwid[2].strip('SER='), 16)

					if usb_serial_number == self.scanner_config['serial_base']:
						continue

				if port_full_name.startswith(self.serial_ports_prefix):
					self.se[port_full_name] = serial.Serial()
					self.se[port_full_name].baudrate = self.serial_baudrate
					self.se[port_full_name].port = port_full_name
					self.se[port_full_name].open()

					time.sleep(0.1)
					self.se[port_full_name].flushInput()
					self.se[port_full_name].flushOutput()

					print('\t- Port {} initialized.'.format(port_full_name))

		else:
			self.se['P0'] = None
			print('\t- Port P0 initialized [DEBUG].')

		print('{} port(s) initialized.'.format(len(self.se)))
		print('------------------------------')


	def closePorts(self):
		if not self.debug:
			for port_name in self.se:
				try:
					self.se[port_name].close()
				except Exception as e:
					print('Cannot close port {}: {}'.format(port_name, e))


	def startProcesses(self):

		for thread in self.threads:
			thread.start()

		for thread in self.threads:
			thread.join()


if __name__ == '__main__':

	farmManager = None

	try:
		farmManager = FarmManager('config.yaml')
		farmManager.startProcesses()

	except Exception as e:
		print('Error:', e)

	finally:
		if farmManager is not None:
			farmManager.closePorts()
