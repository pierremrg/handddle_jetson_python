import threading
import serial
import serial.tools.list_ports as port_list
import time
import webbrowser

from messages.tlv_message import TLVMessage

######################
# Smart Farm Scanner #
######################

class ScannerThread(threading.Thread):
	def __init__(self, scanner_config, api_server_config, debug):
		threading.Thread.__init__(self)
		self.scanner_serial_base = scanner_config['serial_base']
		self.scanner_baudrate = scanner_config['baudrate']
		self.api_server_config = api_server_config
		self.debug = debug

		self.scanner = None
		self.checkUSBScanner()

	def checkUSBScanner(self):
		ports = list(port_list.comports())

		for port_name, description, hwid in ports:
			try:
				hwid = hwid.split()

				if len(hwid) > 2 and hwid[2].startswith('SER='):
					usb_serial_number = int(hwid[2].strip('SER='), 16)

					if usb_serial_number == self.scanner_serial_base:
						self.scanner = serial.Serial(port_name, self.scanner_baudrate)

			except Exception as e:
				self.scanner = None
				print('Error while reading "{}" port serial number. (Details: {})'.format(port_name, e))

	def closePorts(self):
		if self.scanner is not None:
			try:
				self.scanner.close()
			except Exception as e:
				print('Cannot close scanner port {}: {}'.format(port_name, e))

	def run(self):

		if self.scanner is None:
			return

		print('Started ScannerThread')

		while True:
			time.sleep(0.5)
			try:
				if self.scanner.in_waiting:

					barCode = b''
					while self.scanner.in_waiting:
						barCode += self.scanner.read(1)
						time.sleep(0.001)

					barCode = barCode.decode('utf-8').strip()
					webbrowser.open(
						self.api_server_config['protocol'] + '://' + self.api_server_config['host'] + '/resources/' + barCode,
						new=0
					)

			except Exception as e:
				print('ERROR: An error occured while dealing with scanner data.')
				break

		self.closePorts()
