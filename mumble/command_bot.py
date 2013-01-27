#!/bin/python
#
# Bot that can answers to !... commands.
# How to use:
#   Inherits from CommandBot and override on_command.
#   The rest of the Bot interface remains inchanged.
#
# In mumble, you can use the command_prefixes to make a call.
# The default commands are prefixed with '!', ie. '!ban other_user'.
# To implement different prefixes, you must pass a dictionary to __init__ which
# has keys for the prefix and methods to be called for the value.
#
# The method will be called with list of arguments in order, containing
# containing prefix. So for the example above and by default, it will call
#   CommandBot.on_command(self, '!ban', 'other_user')
#
# Manage that as you will.

import logging
import re
import shlex
import time

from bot import Bot

LOGGER = logging.getLogger(__name__)

class CommandBot(Bot):
  DEFAULT_PREFIXES = {
    '!': 'on_command',
  }

  def __init__(self, command_prefixes = CommandBot.DEFAULT_PREFIXES,
                     name = "CommandBot by HansL"):
    Bot.__init__(self, name = name)
    self.__prefixes = command_prefixes

  def on_text_message(self, from, user_ids, channel_ids, tree_ids, message):
    # Only answer to direct messages, not channel messages.
    if self.state.session_id in user_ids:
      cmd = shlex.split(m.group(1))
      for p in self.__prefixes.keys():
        if cmd[0].startswith(p):
          getattr(self, __prefixes[p])(self, from = from, *cmd)
          return
    Bot.on_text_message(self, from, user_ids, channel_ids, tree_ids, message)

  def on_command(self, from, *args):
    pass