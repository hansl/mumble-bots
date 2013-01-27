#!/bin/python
#
# Simple bot that repeats whatever text message was sent to it after a delay,
# on a potentially different channel.
#

import logging
import sys
import threading
import time

import mumble

class EveBot(mumble.CommandBot):
  def __init__(self, server, name = "EchoBot by HansL"):
    mumble.CommandBot.__init__(self, server, name = name)
    self.relays = {}

  def start(self, server, nickname, prefix_relay):
    

  def on_command_text(self, from_id, command, args):
    print "Command '%s'('%s')" % (command, args)
    return True  # Do not echo.

  def on_voice_talk(self, from_id, sequence, data):
    print "Received voice: %d bytes" % len(data)
