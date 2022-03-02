import threading
import time
import os
from os.path import dirname, abspath
from flask import Flask, render_template
from datetime import datetime
import requests

from messages.tlv_message import TLVMessage

##################
# Smart Farm GUI #
##################

class GUIThread(threading.Thread):
	def __init__(self, uids, api_server_config, status_dict, transfer_queue, debug):
		threading.Thread.__init__(self)
		self.uids = uids
		self.api_server_config = api_server_config
		self.status_dict = status_dict
		self.transfer_queue = transfer_queue
		self.debug = debug

	def run(self):

		print('Started GUIThread')

		template_folder = dirname(dirname(abspath(__file__))) + '/templates/'
		app = Flask(__name__, template_folder=template_folder)
		app.debug = False
		app.use_reloader = False

		@app.route('/')
		def index():
			start_date = datetime.now()
			devices = []

			for uid, device in self.status_dict.items():
				devices.append({
					'uid': uid,
					'system_code': device['system_code'],
					'port': device['port'],
					'check_date': device['check_date'].strftime("%d/%m/%Y %H:%M:%S"),
					'status': 'OK' if time.time() - device['check_date'].timestamp() < 30 else 'Error'
				})

			for uid, system_code in self.uids.items():
				if uid not in self.status_dict and system_code != 'broadcast':
					devices.append({
						'uid': uid,
						'system_code': system_code,
						'port': 'Not detected',
						'check_date': '-',
						'status': 'Error'
					})

			r = self.api_server_config['session'].get(
				url=self.api_server_config['protocol'] + '://' + self.api_server_config['host'] + '/public/api/farm_commands',
				params={
					'organization_group.code': self.api_server_config['licence_key'],
					'sent_date[gte]': int(datetime.now().timestamp())
				},
				timeout=10
			)

			return render_template(
				'index.html',
				check_date=start_date.strftime("%d/%m/%Y %H:%M:%S"),
				app_host=self.api_server_config['host'],
				app_check_date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
				app_status='OK' if r.status_code == 200 else 'Error',
				devices=devices
			)

		@app.route('/open_doors')
		def open_doors():
			broadcast_uid = 'CFFFFFFF'
			for uid, system_code in self.uids.items():
				if system_code == 'broadcast':
					broadcast_uid = uid

			message, hexa = TLVMessage.createTLVCommandFromJson(
				broadcast_uid, 'door_closed', 0
			)
			self.transfer_queue.put(message)

			return {'success': True}

		app.run(host='127.0.0.1', port=8080)