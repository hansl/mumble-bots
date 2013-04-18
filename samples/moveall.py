#!/bin/python
#
# Simple bot that will move all users on the server to a channel
# when issued the command /moveall.
# Set the channel ID with /set channel_id 1
# Or the channel name with /set channel_name "the name"
# You can manage the rights of this bot by sending it the
# /add_right message, e.g. /add_right UserName moveall
# or /remove_right.
import mumble

import sys

class UserMoveBot(mumble.AdvanceBot):
  def __init__(self, name = "EchoBot by HansL"):
    mumble.AdvanceBot.__init__(self, name = name)
    self.args = {'channel_id': 0}
    self.all_rights = ['get', 'set', 'moveall']

  def stopping(self):
    self.thread.keep_going = False

  def on_command_moveall(self, *_):
    for user in self.users():
      user.move_to(self.get_channel_by_id(self.var["channel_id"]))

if __name__ == '__main__':
  # Start the bot
  bot = UserMoveBot()
  bot.start(mumble.Server(sys.argv[1], sys.argv[2]), "-Bot-")
  bot.join()
