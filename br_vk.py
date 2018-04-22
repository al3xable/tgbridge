import json
import threading
import requests
import sys
from vk.exceptions import VkAPIError

from bridge import Bridge
import vk


class VkBridge(Bridge):
	api = {}
	user = {}

	def __init__(self, name, tg):
		Bridge.__init__(self, name, tg)

		self.api = vk.API(vk.Session(access_token=self.cfg['token']), v='5.74', lang='ru', timeout=10)
		self.user = self.api.users.get()[0]

		thr = threading.Thread(target=self.poll)
		thr.daemon = True
		thr.start()

	def poll(self):
		try:
			lp = self.api.messages.getLongPollServer()
			self.log.info('VK ready.')

			server, key, ts = lp['server'], lp['key'], lp['ts']
			while True:
				r = requests.get(
					"https://%s?act=a_check&key=%s&ts=%s&wait=25&mode=2&version=3" % (server, key, ts)).json()
				ts = r['ts']

				for upd in r['updates']:
					if upd[0] == 4:
						flags = []
						for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:
							if upd[2] & number:
								flags.append(number)

						if 0 in flags:
							continue

						id = upd[3]
						title = 'PEER ' + str(id)
						message = upd[5]

						if id < 0:  # GROUP
							group = self.api.groups.getById(group_id=abs(id))[0]
							title = group['name']

						elif id > 2000000000:  # CHAT
							chat = self.api.messages.getChat(chat_id=id - 2000000000)
							user = self.api.users.get(user_id=upd[6]['from'])[0]
							title = "[%s:%i] %s %s (ID:%i)" % (
								chat['title'], id, user['first_name'], user['last_name'], user['id'])

						elif id > 0:  # USER
							user = self.api.users.get(user_id=id)[0]
							title = "%s %s (ID:%i)" % (user['first_name'], user['last_name'], user['id'])

						self.tg.push(name=self.name, title=title, chat_id=id, text=message)
		except VkAPIError as e:
			print(e.request_params)
			self.log.error('Poll error: ' + e.message)
			self.tg.push(name=self.name, title='ERROR', text=e.message)
		except:  # catch *all* exceptions
			e = sys.exc_info()[0]
			print(e)
			self.tg.push(name=self.name, title='ERROR', text=str(e))
		finally:
			self.poll()

	def send(self, chat_id, text):
		Bridge.send(self, chat_id=chat_id, text=text)
		try:
			self.api.messages.send(peer_id=chat_id, message=text)
		except VkAPIError as e:
			self.log.error('Error while send message: ' + e.message)
