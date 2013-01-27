import logging

LOGGER = logging.getLogger(__name__)

class Channel(object):
  def __init__(self, bot, id):
    self.bot = bot
    self.id = id
    self.parent = None
    self.children = {}
    self.users = {}
    self.links = {}

  def get_children(self):
    return self.children.values()

  def get_users(self):
    return self.users.values()

  def join(self):
    self.bot.join_channel(self.id)

  def add_user(self, user):
    assert user.session not in self.users
    self.users[user.session] = user

  def remove_user(self, user):
    assert user.session in self.users
    del self.users[user.session]

  def remove_child(self, chan):
    if chan.parent != self:
      LOGGER.warning("Removing a channel (%d) from a different parent (%d)" % (
                      chan.id, self.id))
      return
    chan.parent = None
    del self.children[chan.id]

  def add_child(self, chan):
    if chan.id in self.children:
      return
    if chan.parent:
      chan.parent.remove_child(chan)
    chan.parent = self
    self.children[chan.id] = chan

  def update(self, msg):
    if msg.name: self.name = msg.name
    if msg.description:
      self.description = msg.description
    elif msg.description_hash:
      self.description = self.bot.connection.ask_description_for_channel(self.id)

    self.temp = msg.temporary
    self.position = msg.position
    self.links = {}
    for l in msg.links:
      chan = self.bot.get_channel_by_id(l)
      assert chan
      self.links[l] = chan
