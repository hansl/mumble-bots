#!/bin/python
#
# Simple bot that repeats whatever text message was sent to it after a delay.
#

from optparse import OptionParser

import logging
import sys
import threading
import time

import mumble

class EchoBot(mumble.CommandBot):
  def __init__(self, server, name = "EchoBot by HansL"):
    mumble.CommandBot.__init__(self, server, name = name)

  # When a text message is receive from user to user, we create a new thread
  # that waits and send a new message back to the user.
  def on_message_self(self, from_id, message):
    bot = self
    print "Received message: ", message
    class EchoThread(threading.Thread):
      def run(self):
        time.sleep(1)
        bot.send_message(destination = from_id, message = message)
    tr = EchoThread()
    tr.run()

  def on_command_text(self, from_id, command, args):
    print "Command '%s'('%s')" % (command, args)
    return True  # Do not echo.
