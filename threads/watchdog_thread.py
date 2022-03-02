import threading
import time

from messages.tlv_message import TLVMessage

#######################
# Smart Farm Watchdog #
#######################

class WatchdogThread(threading.Thread):
	def __init__(self, interval, transfer_queue, uids, debug):
		threading.Thread.__init__(self)
		self.transfer_queue = transfer_queue
		self.uids = uids
		self.debug = debug

		self.interval = interval
		self.count = 0

		self.broadcast_uid = 'CFFFFFFF'
		for uid, system_code in self.uids.items():
			if system_code == 'broadcast':
				self.broadcast_uid = uid

	def run(self):

		print('Started WatchdogThread')

		while True:  # Infinite loop
			try:
				self.count += 1
				time.sleep(1)

				# Watchdog update
				if self.count >= self.interval:
					message, hexa = TLVMessage.createTLVCommandFromJson(
						'CFFFFFFF', 'update_watchdog', 1
					)

					self.count = 0
					self.transfer_queue.put(message)


			except Exception as e:
				print('ERROR: An error occured while sending the watchdog command.')