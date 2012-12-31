#!/bin/python

import logging

LOGGER = logging.getLogger(__name__)

class Channel(object):
  def __init__(self, id):
    self.id = id
    self.parent = None
    self.children = {}

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

  def update(self, name, description, is_temporary, position):
    self.name = name
    self.description = description
    self.temp = is_temporary
    self.position = position
