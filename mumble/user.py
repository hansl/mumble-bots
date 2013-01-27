class UserStats(object):
  def __init__(self, good=0, late=0, lost=0, resync=0):
    self.good = good
    self.late = late
    self.lost = lost
    self.resync = resync
  def update(self, good=None, late=None, lost=None, resync=None):
    if good: self.good = good
    if late: self.late = late
    if lost: self.lost = lost
    if resync: self.resync = resync

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
    self.from_client = UserStats()
    self.from_server = UserStats()
    self.onlinesecs = 0
    self.idlesecs = 0

  def is_superuser(self):
    return self.id == 0

  def move_to(self, channel):
    self.bot.connection.move_user_to_channel(self.session, channel.id)

  def update_stats(self, msg):
    assert msg.session == self.session
    self.onlinesecs = msg.onlinesecs
    self.idlesecs = msg.idlesecs
    self.from_client.update(msg.from_client.good, msg.from_client.late,
                            msg.from_client.lost, msg.from_client.resync)
    self.from_server.update(msg.from_server.good, msg.from_server.late,
                            msg.from_server.lost, msg.from_server.resync)

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
      self.bot.connection.ask_comment_for_user(self.session)
      # The callback will set it automatically.
    self.bot.connection.ask_stats_for_user(self.session)

