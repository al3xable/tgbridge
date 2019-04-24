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
        while True:
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

                            # if 2 in flags:
                            #	continue

                            id = upd[3]
                            title = 'PEER ' + str(id)
                            message = upd[5]

                            msg = self.api.messages.getHistory(peer_id=id, start_message_id=upd[1], count=1)['items'][0]

                            if id < 0:  # GROUP
                                group = self.api.groups.getById(group_id=abs(id))[0]

                                if id == msg['from_id']:
                                    title = "%s (ID:%i)" % (
                                        group['name'], id)
                                else:
                                    user = self.api.users.get(user_id=msg['from_id'])[0]
                                    title = "%s %s (%i) » %s (%i)" % (
                                        user['first_name'], user['last_name'], user['id'], group['name'], id)

                            elif id > 2000000000:  # CHAT
                                chat = self.api.messages.getChat(chat_id=id - 2000000000)
                                user = self.api.users.get(user_id=upd[6]['from'])[0]
                                title = "%s %s (%i) » %s (%i)" % (
                                    user['first_name'], user['last_name'], user['id'], chat['title'], id)

                            elif id > 0:  # USER
                                user = self.api.users.get(user_id=msg['from_id'])[0]
                                chat = self.api.users.get(user_id=id)[0]
                                if id == msg['from_id']:
                                    title = "%s %s (%i)" % (
                                        user['first_name'], user['last_name'], user['id'])
                                else:
                                    title = "%s %s (%i) » %s %s (%i)" % (
                                        user['first_name'], user['last_name'], user['id'], chat['first_name'],
                                        chat['last_name'], id)

                            self.tg.push(name=self.name, title=title, chat_id=id, text=message)

                            try:
                                for at in msg['attachments']:
                                    if at['type'] == 'photo':
                                        self.tg.push(name=self.name, title=title, chat_id=id, text="<PHOTO>",
                                                     photo=at['photo']['photo_604'])
                                    elif at['type'] == 'doc':
                                        self.tg.push(name=self.name, title=title, chat_id=id, text="<DOCUMENT>",
                                                     document=at['doc']['url'])
                                    elif at['type'] == 'audio':
                                        title = "%s - %s" % (at['audio']['artist'], at['audio']['title'])
                                        self.tg.push(name=self.name, title=title, chat_id=id, text="<AUDIO> " + title,
                                                     audio=at['audio']['url'], audio_title=title)
                                    else:
                                        print(at)
                                        self.tg.push(name=self.name, title=title, chat_id=id,
                                                     text="<%s>" % (at['type'].upper()))
                            except:
                                pass
            except VkAPIError as e:
                print(e.request_params)
                self.log.error('Poll error: ' + e.message)
            except:  # catch *all* exceptions
                e = sys.exc_info()[0]
                print(e)

    def send(self, chat_id, text):
        Bridge.send(self, chat_id=chat_id, text=text)
        try:
            self.api.messages.send(peer_id=chat_id, message=text)
        except VkAPIError as e:
            self.log.error('Error while send message: ' + e.message)
