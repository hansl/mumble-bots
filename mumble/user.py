#!/bin/python

class User(object):
  def __init__(self, bot, session_id):
    self.bot = bot
    self.channel = None
    self.session = session_id
    self.id = None
    self.is_superuser = False
    self.is_muted = False
    self.is_deaf = False
    self.is_suppressed = False

  def update(self, msg):
    assert msg.session == self.session
    if msg.name: self.name = msg.name
    if msg.user_id is not None:
      self.id = msg.user_id
      self.is_superuser = msg.user_id == 0
    if msg.channel_id is not None:
      chan = self.bot.get_channel_by_id(msg.channel_id)
      if not self.channel:
        chan.add_user(self)
      elif self.channel.id != chan.id:
        self.channel.remove_user(self)
        chan.add_user(self)
      self.channel = chan

    if msg.mute: self.is_muted = msg.mute
    if msg.deaf: self.is_deaf = msg.deaf
    if msg.suppress: self.is_suppressed = msg.suppress

    if msg.comment:
      self.comment = msg.comment
    elif msg.comment_hash:
      self.comment_hash = msg.comment_hash
      self.bot.connection.ask_comment_for_user(self.user_id)
      # The callback will set it automatically.

