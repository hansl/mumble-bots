#!/bin/python
#
# The most advance bot to inherit from, this one answers to events, manage
# internal state (set/get arguments), rights and serialization of all that.
#
# How to use:
#   Inherits from AdvanceBot and generate your own on_command_*. For an
#   example, see on_command_set() and on_command_get().

import logging
import pickle
import re
import shlex
import time

from command_bot import CommandBot

LOGGER = logging.getLogger(__name__)

class AdvanceBot(CommandBot):
  """Advanced Bot that can execute commands to get / set variables and
  also manage rights for those (or any subclass) commands.

  Also manage permanent data that gets loaded/saved to a config file
  automatically.
  """

  PREFIXES = {
    '!': 'on_command_bang',
    '/': 'on_command_slash',
  }

  def __init__(self, config_path = None, name = 'AdvanceBot by HansL'):
    """
    Arguments: config_path The config path, or None to use the default. You can
                           manually load/save the config path later.
               name The name of the bot (version).
    """
    Bot.__init__(self, name = name)
    self.var = {}
    self.rights = {}
    self.all_rights = []  # Rights by everyone
    # These are never serialized because sessions vary from login/logout.
    self.__session_rights = {}
    self.__config_path = config_path
    if self.__config_path: self.load_config(self.__config_path)

  def __del__(self):
    if self.__config_path: self.save_config(self.__config_path)

  def load_config(self, path):
    """Reload the config (overriding it) from path."""
    with open(path, 'r') as fin:
      (self.var, self.rights, self.all_rights) = pickle.load(fin)

  def save_config(self, path):
    """Save the full config, except session data, to path."""
    with open(path, 'w') as fout:
      pickle.dump((self.var, self.rights, self.all_rights), fout)

  def check_rights(self, from, command):
    """Returns true if the command is available for the specified user."""
    if from.id is None:
      if from.session in self.__session_rights:
        return command in self.__session_rights[from.session]
    else:
      if from.id in self.rights:
        return command in self.rights[from.id]
    if from.is_superuser():
      # Superuser can do everything, except if you specifically block him above.
      return True
    return command in self.all_rights

  def on_command_set(self, from, name, value, *_):
    """Set a local variable."""
    self.var[name] = value
    self.send_message(from, '\'%s\' = \'%s\'' % (name, self.var[name]))

  def on_command_get(self, from, name, *_):
    self.send_message(from, '\'%s\' = \'%s\'' % (name, self.var[name]))

  def on_command_add_right(self, from, name, command, *_):
    target = self.get_user_by_name(name)
    if target is None:
      self.send_message(from, 'User not found: \'%s\'' % name)
    if target.id is None:
      if not target.session in self.__session_rights:
        self.__session_rights[target.session] = [command]
      else:

      self.send_message(from, 'Temporarily set right for user.')
    else:
      if from.id not in self.rights:


  def on_command_slash(self, from, command, kargs):
    if self.check_rights(from, command):
      func = getattr(self, 'command_%s' % command, None)
      if func:
        func(from, *kargs)
    return True

  def on_command_bang(self, from, command, args):
    return False