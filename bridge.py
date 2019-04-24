import logging


class Bridge:
    name = 'bridge'
    cfg = {}
    tg = {}
    log = {}

    def __init__(self, name, tg):
        self.name = name
        self.tg = tg
        self.cfg = tg.cfg[name]
        self.log = logging.getLogger(__name__ + '.' + name)

    def send(self, chat_id, text):
        self.log.info('Sending to chat ' + str(chat_id) + ': ' + text)
