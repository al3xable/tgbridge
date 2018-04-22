import json
import logging

from telegram import ParseMode
from telegram.ext import Updater, MessageHandler, Filters

from br_vk import VkBridge


class TgBridge:
	cfg = json.loads(open('config.json', 'r').read())
	log = logging.getLogger(__name__)

	tg = None
	vk = None

	def push(self, name, title, text):
		self.log.info('[' + name + '] ' + title + ': ' + text)
		msg = '*%s> %s:*\n%s' % (name.upper(), title, text)
		self.tg.send_message(chat_id=self.cfg['telegram']['master'], text=msg,
							 parse_mode=ParseMode.MARKDOWN)

	def tg_message(self, bot, update):
		if update.message.from_user.id != self.cfg['telegram']['master']:
			return

		cmd = update.message.text.split(' ', 2)
		if len(cmd) != 3:
			update.message.reply_text('Usage: <name> <chat> <message>')
			return

		# VK MESSAGE
		if cmd[0] == 'vk':
			self.vk.send(chat_id=cmd[1], text=cmd[2])

	def start(self):
		logging.basicConfig(format=self.cfg['general']['log_format'], level=logging.INFO,
							filename=self.cfg['general']['log_file'])

		# VK INIT
		self.vk = VkBridge('vk', self)

		# TELEGRAM BOT INIT
		updater = Updater(self.cfg['telegram']['token'])
		self.tg = updater.bot

		updater.dispatcher.add_handler(MessageHandler(Filters.text, self.tg_message))
		# updater.dispatcher.add_handler(MessageHandler(Filters.photo, self.tg_photo))

		updater.start_polling(timeout=self.cfg['telegram']['pool_timeout'],
							  network_delay=self.cfg['telegram']['network_delay'])
		self.log.info('Telegram ready.')
		updater.idle()


if __name__ == '__main__':
	TgBridge().start()
