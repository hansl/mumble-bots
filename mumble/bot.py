import logging

from channel import Channel
from connection import Connection
from permissions import Permissions
from user import User

LOGGER = logging.getLogger(__name__)

# All the server state is kept in the delegate. The Bot itself is basically
# a delegate of BotState. This is to simplify the logic of bots to the
# highest logic needed, without clutter.
# It's a passive state machine.
class BotState(object):
  def __init__(self, bot):
    self.bot = bot
    self.channels_by_id = {}
    self.users_by_session = {}
    self.users_by_id = {}
    self.root = None
    self.permissions = None
    # The user object representing the bot.
    self.user = None
    # The current channel the bot is in.
    self.channel = None

  def get_actor(self, session_id):
    if not session_id in self.users_by_session:
      LOGGER.warning('Invalid session ID: %d.' % session_id)
      return None
    else:
      return self.users_by_session[session_id]

  def get_channel(self, chan_id):
    if not chan_id in self.channels_by_id:
      LOGGER.warning('Invalid Channel ID: %d.' % chan_id)
      return None
    else:
      return self.channels_by_id[chan_id]

  def on_version(self, msg):
    self.version = msg.version
    self.release = msg.release
    self.os = msg.os
    self.os_version = msg.os_version

  def on_voice_ping(self, session_id):
    self.bot.on_voice_ping(session_id)

  def on_voice_talk(self, from_id, sequence, data):
    self.bot.on_voice_talk(self.get_actor(from_id), sequence, data)

  def on_voice_whisper_chan(self, from_id, sequence, data):
    pass

  def on_voice_whisper_self(self, from_id, sequence, data):
    pass

  def on_pingback(self, ping_msec, msg):
    self.ping = ping_msec
    self.packet_stats = (msg.good, msg.late, msg.lost)
    self.udp_stats = (msg.udp_packets, msg.udp_ping_avg, msg.udp_ping_var)

  def on_reject(self, msg):
    self.rejected = True
    self.reject_type = msg.type
    self.reject_reason = msg.reason
    self.bot.rejected()

  def on_server_config(self, msg):
    self.welcome_text = msg.welcome_text
    self.allow_html = msg.allow_html

  def on_server_sync(self, msg):
    self.max_bandwidth = msg.max_bandwidth
    self.welcome_text = msg.welcome_text
    if msg.permissions:
      if not self.permissions:
        self.permissions = Permissions(msg.permissions)
      else:
        self.permissions.update(msg.permissions)
    self.bot.connected()

  def on_channel_state(self, msg):
    if msg.channel_id not in self.channels_by_id:
      chan = Channel(self.bot, msg.channel_id)
      self.channels_by_id[msg.channel_id] = chan
    else:
      chan = self.channels_by_id[msg.channel_id]
    chan.update(msg)

    if msg.parent == msg.channel_id:
      if not msg.channel_id == 0:
        LOGGER.warning('Root channel not ID 0.')
      if self.root and self.root != chan:
        LOGGER.error('Received 2 different roots...?')
        raise Exception('Two roots.')
      self.root = chan
    elif chan.parent:
      if chan.parent.id != msg.parent:
        chan.parent.remove_child(chan)
        self.channels_by_id[msg.parent].add_child(chan)
    else:
      if not msg.parent in self.channels_by_id:
        LOGGER.error('Parent ID passed by server is not in the channel list.')
        raise Exception('Invalid Parent.')
      self.channels_by_id[msg.parent].add_child(chan)

  def on_user_state(self, msg):
    if msg.session not in self.users_by_session:
      user = User(self.bot, msg.session)
      self.users_by_session[msg.session] = user
      if msg.user_id is not None:
        self.users_by_id[msg.user_id] = user
    else:
      user = self.users_by_session[msg.session]
    user.update(msg)
    if self.user is None:
      self.user = user

  def on_text_message(self, msg):
    self.bot.on_text_message(from_user = self.get_actor(msg.actor),
                             to_users = [self.get_actor(x)
                                 for x in msg.session],
                             to_channels = [self.get_channel(x)
                                 for x in msg.channel_id],
                             tree_ids = msg.tree_id,
                             message = "%s" % msg.message)

  def on_crypt_setup(self, msg):
    pass

  def on_user_stats(self, msg):
    assert msg.session in self.users_by_session
    self.users_by_session[msg.session].update_stats(msg)

  def on_unknown(self, type, msg):
    LOGGER.warning("Unknown message received: type(%s), '%s'" % (type, msg))

# The root class of any bots. This provides more utility over connection and
# keep the bot state. It also builds the BotState for the connection for you,
# so you don't have to (ain't that nice).
class Bot(object):
  def __init__(self, version = "HansBot"):
    self.version = version
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

  def send_message(self, user, message):
    self.connection.send_message(destination = user.session, message = message)

  def stop(self):
    self.connection.stop()
    self.connection = None

  def rejected(self):
    self.stop()

  def connected(self):
    pass

  def channels(self):
    return self.state.channels_by_id.values()

  def users(self):
    return self.state.users_by_session.values()

  def get_channel_by_id(self, id):
    return self.state.channels_by_id[id]

  def get_user_by_id(self, id):
    return self.state.users_by_id[id]

  def get_user_by_name(self, name):
    for u in self.state.users_by_session:
      if self.state.users_by_session[u].name == name:
        return self.state.users_by_session[u]
    return None

  def get_root(self):
    return self.state.root

  def is_connected(self):
    return self.connection is not None

  ##############################################################################
  ### EVENTS FROM STATE
  def on_text_message(self, from_user, to_users, to_channels, tree_ids,
                      message):
    if self.state.user.session in to_users:
      self.on_message_self(from_user = from_user, message = message)
    if to_users:
      self.on_message_users(from_user = from_user, to_users = to_users,
                            message = message)
    if to_channels:
      self.on_message_channels(from_user = from_user, to_channels = to_channels,
                               message = message)
    if tree_ids:
      self.on_message_trees(from_user = from_user, tree_ids = tree_ids,
                            message = message)

  def on_voice_ping(self, session_id):
    pass
  def on_voice_talk(self, from_user, sequence, data):
    pass

  ##############################################################################
  ### EVENTS
  def on_message_self(self, from_user, message):
    pass
  def on_message_users(self, from_user, to_users, message):
    pass
  def on_message_channels(self, from_user, to_channels, message):
    pass
  def on_message_trees(self, from_user, tree_ids, message):
    pass
