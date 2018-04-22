import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

from br_vk import VkBridge


class TgBridge:
	cfg = json.loads(open('config.json', 'r').read())
	cfg_tg = cfg['telegram']
	log = logging.getLogger(__name__)
	active = None

	tg = None
	vk = None

	def push(self, name, title, chat_id, text):
		self.log.info('[' + name + '] ' + title + ': ' + text)
		msg = '*%s> %s:*\n%s' % (name.upper(), title, text)

		if self.active and self.active[0] == name and self.active[1] == str(chat_id):
			rm = None
		else:
			rm = InlineKeyboardMarkup(
				[[InlineKeyboardButton("Set this chat active", callback_data='set_active:' + name + ':' + str(chat_id))]])

		self.tg.send_message(chat_id=self.cfg_tg['master'], text=msg, parse_mode='MARKDOWN', reply_markup=rm)

	def tg_button(self, bot, update):
		query = update.callback_query
		chat = query.message.chat_id
		data = query.data.split(':')

		if data[0] == 'set_active':
			self.active = [data[1], data[2]]
			bot.edit_message_reply_markup(chat_id=chat, message_id=query.message.message_id, reply_markup=None)
			bot.send_message(chat_id=chat, text='Chat %s from %s is now active' % (data[2], data[1]))

	def tg_message(self, bot, update):
		if update.message.from_user.id != self.cfg['telegram']['master']:
			return

		if self.active:
			cmd = list(self.active)
			cmd.append(update.message.text)
		else:
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
		updater = Updater(self.cfg_tg['token'])
		self.tg = updater.bot

		updater.dispatcher.add_handler(MessageHandler(Filters.text, self.tg_message))
		# updater.dispatcher.add_handler(MessageHandler(Filters.photo, self.tg_photo))
		updater.dispatcher.add_handler(CallbackQueryHandler(self.tg_button))

		updater.start_polling(timeout=self.cfg_tg['pool_timeout'], read_latency=self.cfg_tg['read_latency'])
		self.log.info('Telegram ready.')
		updater.idle()


if __name__ == '__main__':
	TgBridge().start()
