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
    '!': 'on_bang',
    '/': 'on_slash',
  }
  DATA_VERSION = 0

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
    """Reload the config (overriding it) from path.

      Arguments: path The path of the config to load (does not force save later.
    """
    with open(path, 'r') as fin:
      data = pickle.load(fin)
      if (data['version'] >= 0):
        self.var = data['var']
        self.rights = data['rights']
        self.all_rights = data['all_rights']

  def save_config(self, path):
    """Save the full config, except session data, to path.

      Arguments: path The path of the config to save to.
    """
    with open(path, 'w') as fout:
      pickle.dump({
        version: AdvanceBot.DATA_VERSION,
        var: self.var,
        rights: self.rights,
        all_rights: self.all_rights,
      }, fout)

  def has_rights(self, from, command):
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
    """Get the value of a local variable."""
    self.send_message(from, '\'%s\' = \'%s\'' % (name, self.var[name]))

  def on_command_add_right(self, from, name, command, *_):
    target = self.get_user_by_name(name)
    if target is None:
      self.send_message(from, 'User not found: \'%s\'' % name)
    if target.id is None:
      if not target.session in self.__session_rights:
        self.__session_rights[target.session] = Set()
      self.__session.rights[target.session].insert(command)
      self.send_message(from, 'Temporarily set right for user.')
    else:
      if from.id not in self.rights:
        self.rights[from.id] = Set()
      self.rights[from.id].insert(command)
      self.send_message(from, 'Permanently set right for user.')

  def on_command_list_commands(self, from, *_):
    """List all commands supported by this bot."""
    commands = filter(lambda x: x.startswith('on_command_'),
                      self.__dict__.keys())
    

  def on_command_help(self, from, command=None, *_):
    """Provides help for functions.
       Use /help [command] to get the documentation of a particular command."""
    func = getattr(self, 'command_%s' % command, None)
    if func:
      self.send_message(from, 'Command \'%s\':\n%s' % (command, func.__doc__))
    else:
      self.send_message(from, 'Command \'%s\' not supported.' % command)

  def on_slash(self, from, command, kargs):
    if self.has_rights(from, command):
      func = getattr(self, 'command_%s' % command, None)
      if func:
        func(from, *kargs)
    return True

  def on_bang(self, from, command, args):
    return False