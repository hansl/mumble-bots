#!/bin/python

PERMISSIONS_ = {
  # b'None': 0x0,
  b'Write': 0x1,
  b'Traverse': 0x2,
  b'Enter': 0x4,
  b'Speak': 0x8,
  b'MuteDeafen': 0x10,
  b'Move': 0x20,
  b'MakeChannel': 0x40,
  b'LinkChannel': 0x80,
  b'Whisper': 0x100,
  b'TextMessage': 0x200,
  b'MakeTempChannel': 0x400,

  # Root channel only
  b'Kick': 0x10000,
  b'Ban': 0x20000,
  b'Register': 0x40000,
  b'SelfRegister': 0x80000,

  b'Cached': 0x8000000,
  b'All': 0xf07ff
}

class Permissions(object):
  def __init__(self, p):
    self.update(p)

  def __str__(self):
    ret = []
    for p in PERMISSIONS_:
      if PERMISSIONS_[p] == 0: continue
      if (self.permissions & PERMISSIONS_[p]) == PERMISSIONS_[p]:
        ret += [p]
    return "(%s)" % ",".join(ret)

  def update(self, p):
    self.permissions = p

for p in PERMISSIONS_:
  v = PERMISSIONS_[p]
  def h(self):
    if (self.permissions & v) == v: return True
    return False
  def s(self):
    self.permissions = self.permissions | v
    return self
  def c(self):
    self.permissions = self.permissions ^ (~v)
    return self
  dictionary = {}
  setattr(Permissions, "has_%s" % p.lower(), h)
  setattr(Permissions, "set_%s" % p.lower(), s)
  setattr(Permissions, "clear_%s" % p.lower(), c)
