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

  def __init__(self, command_prefixes = CommandBot.TO.DEFAULT_PREFIXES,
                     channel_command_prefixes =
                         CommandBot.CHAN_DEFAULT_PREFIXES,
                     name = "CommandBot by HansL"):
    Bot.__init__(self, name = name)
    self.__prefixes = command_prefixes
    self.__channel_prefixes = channel_command_prefixes

  def on_text_message(self, from, user_ids, channel_ids, tree_ids, message):
    # Only answer to direct messages, not channel messages.
    if self.state.user.id in user_ids:
      cmd = shlex.split(m.group(1))
      for p in self.__prefixes.keys():
        if cmd[0].startswith(p):
          func = getattr(self, __prefixes[p])
          func(self, from = from, *cmd)
          return
    if self.state.channel.id in channel_ids:
      for p in self.__channel_prefixes.keys():
        if cmd[0].startswith(p):
          func = getattr(self, self.__channel_prefixes[p])
          func(self, from = from, *cmd)
          return
    Bot.on_text_message(self, from, user_ids, channel_ids, tree_ids, message)

  def on_bang(self, from, *args):
    pass