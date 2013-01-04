#!/bin/python
# A console to be used in cmdline. Automates bots.

import atexit
import code
import inspect
import logging
import logging.handlers
import os
import re
import readline
import rlcompleter
import shlex
import sys

import mumble

# Exception used to leave the interactive console from the Context object.
class BotDone(Exception):
  pass


# Context object that define the commands.  Every method of this object is a
# command, except for methods/members that start with _.
# The properties of an instance of this class are considered to be the variables
# usable in the prompt.
class Context(object):
  def __init__(self, bot):
    self.__bot = bot

  def ping(self, hostport):
    (version, users, max_users, bandwidth, ping) = (
        mumble.Server(*hostport.split(':')).ping() or (None, 0, 0, 0, 0))
    if version is None:
      return
    print "Version: %s" % version
    print "Users: %d/%d" % (users, max_users)
    print "Max Bandwidth: %d" % bandwidth
    print "Ping: %d msec" % ping

  def connect(self, hostport, nickname):
    server = mumble.Server(*hostport.split(':'))
    print "Connecting to %s..." % server
    self.__bot.start(server, nickname)

  def disconnect(self):
    self.__bot.stop()

  def exit(self):
    raise BotDone()

  def echo(self, *kwargs):
    print '# '.join(kwargs)

  def list(self, what):
    """@param channels, users"""
    if what == 'channels':
      self._list_channels()

  def show(self, what, arg = None):
    if what == 'user':
      self._show_user(arg)

  def python(self):
    dict = { 'bot': self.__bot }
    code.interact("Python Console. Use quit() to return to bot.", raw_input,
                  dict)

  def _list_channels(self, chan = None, level = 0):
    if not self.__bot.is_connected():
      print "Not connected..."
      return

    if chan is None: chan = self.__bot.state.root
    print "%s'%s' (%d)" % ("   " * level, chan.name, len(chan.users))
    for x in chan.children:
      self._list_channels(chan.children[x], level + 1)

  def _show_user(self, user_id = None):
    if not self.__bot.is_connected():
      print "Not connected..."
      return

    try:
      if user_id is None:
        user = self.__bot.state.user
      else:
        user = self.__bot.get_user_by_id(int(user_id))
    except:
      user = self.__bot.get_user_by_name(user_id)
    if user:
      print "(%s, %d) '%s'" % (user.id or '-', user.session, user.name)
    else:
      print "Could not find user."


# Auto-completion handler.
class Complete(object):
  def __init__(self, context):
    self.context = context
    self.options = [cmd for cmd in context.__class__.__dict__.keys()
                        if cmd and not cmd.startswith('_')]

  def complete(self, text, state):
    response = None
    if state == 0:
      # This is the first time for this text, so build a match list.
      if text:
        self.matches = [s for s in self.options
                          if s and s.startswith(text)]
      else:
        self.matches = self.options[:]

    # Return the state'th item from the match list,
    # if we have that many.
    try:
      response = self.matches[state]
    except IndexError:
      response = None
    return response


# The bot itself.
class InteractiveBot(mumble.Bot):
  def __init__(self, filename = '<console>',
                     histfile = os.path.expanduser("~/.mumblebot_history"),
                     rcfile = os.path.expanduser("~/.mumblebot_rc")):
    mumble.Bot.__init__(self, "HansL InteractiveBot v0.1")
    self.context = Context(self)
    self.prompt = "> "
    self.init_history(histfile)
    self.init_rcfile(rcfile)
    self.init_completion()
    self.init_logging()

  def init_history(self, histfile):
    def save_history(histfile):
      readline.write_history_file(histfile)
    try:
      readline.read_history_file(histfile)
    except IOError:
      pass
    atexit.register(save_history, histfile)

  def init_rcfile(self, rcfile):
    self.rc = None
    try:
      f = open(rcfile, 'r')
      self.rc = f.readlines()
      f.close()
    except IOError:
      pass

  def init_completion(self):
    readline.parse_and_bind('set editing-mode vi')
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("bind ^I rl_complete")
    readline.set_completer(Complete(self.context).complete)

  def init_logging(self):
    logging.basicConfig(format = '%(asctime)s<%(module)s> %(message)s')

  def motd(self):
    print "Welcome to the Mumble Bot Interactive Console!"
    print "Enjoy your stay."
    print

  def execute(self, cmd, *kwargs):
    func = getattr(self.context, cmd, None)
    if not func:
      print "Invalid command '%s'." % cmd
    else:
      # Commands might have optional args
      (args, varargs, _, defaults) = inspect.getargspec(func)
      min_nb = len(args) - len(defaults or []) - 1
      max_nb = len(args) - 1
      if varargs:
        max_nb = sys.maxint

      if len(kwargs) < min_nb or len(kwargs) > max_nb:
        if min_nb == max_nb:
          err = "Expected %d, got %d." % (min_nb, len(kwargs))
        elif max_nb == sys.maxint:
          err = "Expected at least %d, got %d." % (min_nb, len(kwargs))
        else:
          err = ("Expected between %d and %d, got %d."
                 % (min_nb, max_nb, len(kwargs)))
        print("Invalid number of arguments: %s" % err)
      else:
        func(*kwargs)

  def parse_and_execute(self, line):
    # Support for shell-like comments
    cmd = shlex.split(line, True)
    if cmd:
      try:
        self.execute(*cmd)
      except BotDone:
        self.done = True
      except Exception as msg:
        print "Exception: ", msg
      except:
        print "Unknown exception."      

  def interact(self):
    self.done = False
    self.motd()
    for line in self.rc:
      self.parse_and_execute(line)

    while not self.done:
      try:
        line = raw_input(self.prompt)
        self.parse_and_execute(line)
      except EOFError:
        self.done = True
      except KeyboardInterrupt:
        print
        print "Use ^D to quit, or the 'exit' command."
        pass
    print
    if self.connection: self.stop()
