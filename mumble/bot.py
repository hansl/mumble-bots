#!/bin/python

from connection import Connection

# All the server state is kept in the delegate. The Bot itself is basically
# a delegate of BotState. This is to simplify the logic of bots to the
# highest logic needed, without clutter.
# It's a passive state machine.
class BotState(object):
  def __init__(self, bot):
    self._bot = bot

  def on_version(self, version, release, os, os_version):
    self.version = version
    self.release = release
    self.os = os
    self.os_version = os_version

  # We do not support voice right now.
  def on_voice_ping(self, session_id):
    pass
  def on_voice_talk(self, session_id, sequence, data):
    pass
  def on_voice_whisper_chan(self, session_id, sequence, data):
    pass
  def on_voice_whisper_self(self, session_id, sequence, data):
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
    self._bot.rejected()

  def on_server_config(self, welcome_text, allow_html, message_length,
                             image_message_length):
    pass
  def on_server_sync(self, session_id, max_bandwidth, welcome_text,
                           permissions):
    pass
  def on_channel_state(self, channel_id, parent_id, name, links, description,
                             is_temporary, position):
    pass
  def on_crypt_setup(self, key, client, server):
    pass
  def on_unknown(self, type, str):
    print "UNKNOWN"

# The root class of any bots. This provides more utility over connection and
# keep the bot state. It also builds the BotState for the connection for you,
# so you don't have to (ain't that nice).
class Bot(object):
  def __init__(self, server, nickname, name = "MumbleBot 2000"):
    self._state = BotState(self)
    self.connection = Connection(server, nickname, delegate = self._state)
    self.user_id = None
    self.connection.connect()

  def rejected(self):
    self.connection.stop()

