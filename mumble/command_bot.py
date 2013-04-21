#!/bin/python
#
# Bot that can answers to !... commands.
# How to use:
#   Inherits from CommandBot and override on_bang.
#   The rest of the Bot interface remains inchanged.
#
# In mumble, you can use the command_prefixes to make a call.
# The default commands are prefixed with '!', ie. '!ban other_user'.
# To implement different prefixes, you must pass a dictionary to __init__ which
# has keys for the prefix and methods to be called for the value.
#
# The method will be called with list of arguments in order, containing
# containing prefix. So for the example above and by default, it will call
#   CommandBot.on_bang(self, '!ban', 'other_user')
#
# Manage that as you will.

import logging
import re
import shlex
import time

from bot import Bot

LOGGER = logging.getLogger(__name__)

class CommandBot(Bot):
  TO_DEFAULT_PREFIXES = {
    '!': 'on_bang',
  }
  CHAN_DEFAULT_PREFIXES = {}

  def __init__(self, command_prefixes = TO_DEFAULT_PREFIXES,
                     channel_command_prefixes = CHAN_DEFAULT_PREFIXES,
                     name = "CommandBot by HansL"):
    Bot.__init__(self, name)
    self.__prefixes = command_prefixes
    self.__channel_prefixes = channel_command_prefixes

  def on_text_message(self, from_user, to_users, to_channels, tree_ids, message):
    # Only answer to direct messages, not channel messages.
    cmd = shlex.split(message.encode('ascii', 'ignore'))
    if self.state.user in to_users:
      for p in self.__prefixes.keys():
        if cmd[0].startswith(p):
          cmd[0] = cmd[0][len(p):]
          func = getattr(self, self.__prefixes[p])
          func(from_user, *cmd)
          return
    if self.state.channel in to_channels:
      for p in self.__channel_prefixes.keys():
        if cmd[0].startswith(p):
          cmd[0] = cmd[0][len(p):]
          func = getattr(self, self.__channel_prefixes[p])
          func(from_user, *cmd)
          return

    Bot.on_text_message(self, from_user, to_users, to_channels, tree_ids,
                        message)

  def on_bang(self, from_user, *args):
    pass