#!/bin/python
#
# Bot that can answers to /.. commands.
# How to use:
#   Inherits from CommandBot and override on_message_command.
#   The rest of the Bot interface remains inchanged.

import logging
import re
import shlex
import time

from bot import Bot

LOGGER = logging.getLogger(__name__)

class CommandBot(Bot):
  def __init__(self, name = "CommandBot by HansL"):
    Bot.__init__(self, name = name)

  def on_text_message(self, from_id, user_ids, channel_ids, tree_ids, message):
    if self.state.session_id in user_ids:
      cmd = shlex.split(m.group(1))
      if cmd[0][0] == '/':
        if self.on_command_text(from_id = from_id,
                                command = cmd[0][1:],
                                args = cmd[1:]):
          return
      elif cmd[0][0] == '!':
        if self.on_command_bang(from_id = from_id,
                                command = cmd[0][1:],
                                args = cmd[1:]):
          return
    Bot.on_text_message(self, from_id, user_ids, channel_ids, tree_ids, message)

  def on_command_text(self, from_id, command, args):
    return False

  def on_command_bang(self, from_id, command, args):
    return False