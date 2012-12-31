#!/bin/python
#
# Bot that can answers to /.. commands.
# How to use:
#   Inherits from CommandBot and override on_message_command.
#   The rest of the Bot interface remains inchanged.

import logging
import re
import time

from bot import Bot

LOGGER = logging.getLogger(__name__)

class CommandBot(Bot):
  def __init__(self, server, nickname, name = "CommandBot by HansL"):
    # Supports commands like /command-name arg1 arg2
    # Will call on_message_command('command-name', ['arg1', 'arg2'])
    # Also supports bang commands and calls on_message_bang instead.
    self.__cmd = re.compile(r'\s*/(?P<cmd>[a-z][-a-z]+)(?P<args>(\s+\S+)*)\s*')
    self.__bang = re.compile(r'\s*!(?P<cmd>[a-z][-a-z]+)(?P<args>(\s+\S+)*)\s*')
    Bot.__init__(self, server, nickname, name)

  def on_text_message(self, from_id, user_ids, channel_ids, tree_ids, message):
    if self.state.session_id in user_ids:
      m = self.__cmd.search(message)
      if m and self.on_command_text(from_id = from_id,
                                    command = m.group('cmd'),
                                    args = re.split(r'\s+', m.group('args'))):
          return
      m = self.__bang.search(message)
      if m and self.on_command_bang(from_id = from_id,
                                    command = m.group('cmd'),
                                    args = re.split(r'\s+', m.group('args'))):
          return
    Bot.on_text_message(self, from_id, user_ids, channel_ids, tree_ids, message)

  def on_command_text(self, from_id, command, args):
    return False

  def on_command_text(self, from_id, command, args):
    return False