#!/bin/python
#
# Simple bot that moves a user to a different channel if he's been AFK for too long.
# This requires admin rights. The bot will set its own comment if it's inactive.
#

import threading
import time

import mumble

class WatchDogThread(threading.Thread):
  def __init__(self, bot):
    threading.Thread.__init__(self)
    self.keep_going = True
    self.__bot = bot

  def run(self):
    while self.keep_going:
      # Sleep 30 seconds.
      time.sleep(30)
      if self.bot.args['max_idle'] == 0:
        continue
      if not self.bot.get_channel_by_id(self.bot.args['afk_channel']):
        continue

      users = self.__bot.users()
      for u in users:
        if u.idlesecs >= self.bot.args['max_idle']:
          u.move_to(self.__bot.get_channel_by_id(self.bot.args['afk_channel'])

class AfkMoveBot(mumble.CommandBot):
  def __init__(self, server, name = "EchoBot by HansL"):
    mumble.CommandBot.__init__(self, server, name = name)
    self.args = {
      'max_idle': 60
    }

  def connected(self):
    self.thread = WatchDogThread(self)
    self.thread.run()

  def stopping(self):
    self.thread.keep_going = False
