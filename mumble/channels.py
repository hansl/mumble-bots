#!/bin/python
# 

import logger
import platform
import struct

class Channel(object):
  def __init__(self, name, id, parent, position):
    self.name = name
    self.id = id
    self.parent = parent
    self.position = position
    pass

class ChannelTree(object):
  def __init__(self, root):
    pass

  def add(self, channel):
    if channel.tree is not None or channel.tree != self:
      self.logger.warning('')
