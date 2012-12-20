#!/bin/python
# Describes the protocol used to communicate with Mumble.
# This is a series of methods that creates a message to be sent directly
# to Mumble. It's stateless and is just used for convenience.
# It also prevents anyone else from dealing with the pesky Mumble
# protobufs. Instead they just need to call these methods.

import platform
import struct

# Risky modules.
import mumble_pb2


HEADER_FORMAT = ">HI"
HEADER_SIZE = 6
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
TYPE_MESSAGE_LOOKUP = dict((v,k) for k, v in MESSAGE_TYPE_LOOKUP.iteritems())

def serialize_(msg):
  sz = msg.SerializeToString()
  return (struct.pack(HEADER_FORMAT, MESSAGE_TYPE_LOOKUP[type(msg)], len(sz))
          + sz)


# Protobuf Builders.
def version(os = platform.system(), version = ""):
  msg = Mumble_pb2.Version()
  msg.release = "1.2.0"
  msg.version = 66048
  msg.os = os
  msg.os_version = version
  return serialize_(msg)

def authenticate(username, password = None, tokens = None, celt_versions = None,
                 opus = false):
  msg = Mumble_pb2.Authenticate()
  msg.username = username
  if password: msg.password = password
  if tokens: msg.tokens = tokens
  if celt_versions: msg.celt_versions = celt_versions
  if opus: msg.opus = msg.opus
  return serialize_(msg)

# Analyze Packets.
def length_of(header):
  return struct.unpack(HEADER_FORMAT, header)[1]

def parse(header, msg):
  msgType, length = struct.unpack(HEADER_FORMAT, header)
  msgClass = TYPE_MESSAGE_LOOKUP[msgType]
  message = msgClass()
  message.ParseFromString(msg)
  return message

