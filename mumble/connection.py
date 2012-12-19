#!/bin/python

import socket
import sys
import thread
import threading

# Risky modules.
try:
  import Mumble_pb2
except BaseException as e:
  sys.stderr.write("Error while importing: " + str(e) + "\n")
  raise e

HEADER_FORMAT = ">HI"
MESSAGE_TYPE_LOOKUP = {
    Mumble_pb2.Version: 0,
    Mumble_pb2.UDPTunnel: 1,
    Mumble_pb2.Authenticate: 2,
    Mumble_pb2.Ping: 3,
    Mumble_pb2.Reject: 4,
    Mumble_pb2.ServerSync: 5,
    Mumble_pb2.ChannelRemove: 6,
    Mumble_pb2.ChannelState: 7,
    Mumble_pb2.UserRemove: 8,
    Mumble_pb2.UserState: 9,
    Mumble_pb2.BanList: 10,
    Mumble_pb2.TextMessage: 11,
    Mumble_pb2.PermissionDenied: 12,
    Mumble_pb2.ACL: 13,
    Mumble_pb2.QueryUsers: 14,
    Mumble_pb2.CryptSetup: 15,
    Mumble_pb2.ContextActionAdd: 16,
    Mumble_pb2.ContextAction: 17,
    Mumble_pb2.UserList: 18,
    Mumble_pb2.VoiceTarget: 19,
    Mumble_pb2.PermissionQuery: 20,
    Mumble_pb2.CodecVersion: 21,
}

class connection(threading.Thread):
  def __init__(self, server, nickname, password = None):
    self.socket = server.connect()
    self.logger = logging.getLogger(self.__class__.__name__)
    self.mutex  = thread.allocate_lock()

    self.login_()
    self.authenticate_(nickname, password)
    threading.Thread.__init__(self)

  # Privates.
  def send_(self, msg):
    sz = msg.SerializeToString()
    length = len(sz)
    pk = struct.pack(HEADER_FORMAT, MESSAGE_TYPE_LOOKUP[type(msg)], length) + sz
    self.mutex.acquire()


  def login_(self):
    msg = Mumble_pb2.Version()
    msg.release = "1.2.0"
    msg.version = 66048
    msg.os = platform.system()
    msg.os_version = "hBOT 0.1"
    self.send_(msg)

  def authenticate_(self, nick, password):
    msg = Mum

if __name__ == '__main__':

