#!/bin/python

import logging

from channel import Channel
from connection import Connection
from permissions import Permissions

LOGGER = logging.getLogger(__name__)

# All the server state is kept in the delegate. The Bot itself is basically
# a delegate of BotState. This is to simplify the logic of bots to the
# highest logic needed, without clutter.
# It's a passive state machine.
class BotState(object):
  def __init__(self, bot):
    self.bot = bot
    self.channels_by_id = {}
    self.root = None
    # Queue is used if we list channels without a parent. When the parent is
    # added, we add all its children from the queue.
    self._chan_queue = []
    self.permissions = None

  def on_version(self, version, release, os, os_version):
    self.version = version
    self.release = release
    self.os = os
    self.os_version = os_version

  # We do not support voice right now.
  def on_voice_ping(self, session_id):
    pass
  def on_voice_talk(self, from_id, sequence, data):
    pass
  def on_voice_whisper_chan(self, from_id, sequence, data):
    pass
  def on_voice_whisper_self(self, from_id, sequence, data):
    pass

  def on_pingback(self, ping_msec, good, late, lost, udp_packets, udp_ping_avg,
                        udp_ping_var):
    self.ping = ping_msec
    self.packet_stats = (good, late, lost)
    self.udp_stats = (udp_packets, udp_ping_avg, udp_ping_var)

  def on_reject(self, type, reason):
    self.rejected = True
    self.reject_type = type
    self.reject_rease = reason
    self.bot.rejected()

  def on_server_config(self, welcome_text, allow_html, message_length,
                             image_message_length):
    self.welcome_text = welcome_text
    self.allow_html = allow_html

  def on_server_sync(self, session_id, max_bandwidth, welcome_text,
                           permissions):
    self.session_id = session_id
    self.max_bandwidth = max_bandwidth
    self.welcome_text = welcome_text
    if not self.permissions:
      self.permissions = Permissions(permissions)
    else:
      self.permissions.update(permissions)
    self.bot.ready()

  def on_channel_state(self, channel_id, parent_id, name, links, description,
                             is_temporary, position):
    if channel_id not in self.channels_by_id:
      chan = Channel(channel_id)
      self.channels_by_id[channel_id] = chan
    else:
      chan = self.channels_by_id[channel_id]
    chan.update(name, description, is_temporary, position)

    if parent_id == channel_id:
      if self.root is not None and self.root != chan:
        LOGGER.error('Received 2 different roots...?')
        raise Exception('Two roots.')
      self.root = chan
    elif chan.parent:
      if chan.parent.id != parent_id:
        chan.parent.remove_child(chan)
        self.channels_by_id[parent_id].add_child(chan)
    else:
      self.channels_by_id[parent_id].add_child(chan)

  def on_text_message(self, from_id, to, channels, trees, message):
    self.bot.on_text_message(from_id = from_id, user_ids = to,
                             channel_ids = channels, tree_ids = trees,
                             message = message)

  def on_crypt_setup(self, key, client, server):
    pass

  def on_unknown(self, type, str):
    LOGGER.warning("Unknown message received: type(%s), '%s'" % (type, str))

# The root class of any bots. This provides more utility over connection and
# keep the bot state. It also builds the BotState for the connection for you,
# so you don't have to (ain't that nice).
class Bot(object):
  def __init__(self, version = "HansBot"):
    self.version = "HansBot"
    self.state = BotState(self)
    self.connection = None

  def start(self, server, nickname):
    if self.connection:
      LOGGER.warning("Starting the bot twice. Will disconnect old bot.")
      self.stop()
    self.connection = Connection(server, nickname, delegate = self.state,
                                 version = self.version)

  def join(self):
    self.connection.join()

  def send_message(self, destination, message):
    self.connection.send_message(destination = destination, message = message)

  def stop(self):
    self.connection.stop()
    self.connection = None

  def rejected(self):
    self.stop()

  def ready(self):
    pass

  ### EVENTS FROM STATE
  def on_text_message(self, from_id, user_ids, channel_ids, tree_ids, message):
    if self.state.session_id in user_ids:
      self.on_message_self(from_id = from_id, message = message)
    if user_ids:
      self.on_message_users(from_id = from_id, user_ids = user_ids,
                            message = message)
    if channel_ids:
      self.on_message_channels(from_id = from_id, channel_ids = channel_ids,
                               message = message)
    if tree_ids:
      self.on_message_trees(from_id = from_id, tree_ids = tree_ids,
                            message = message)

  ### EVENTS
  def on_message_self(self, from_id, message):
    pass
  def on_message_users(self, from_id, user_ids, message):
    pass
  def on_message_channels(self, from_id, channel_ids, message):
    pass
  def on_message_trees(self, from_id, tree_ids, message):
    pass

