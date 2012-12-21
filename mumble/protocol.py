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
    mumble_pb2.Version: 0,
    mumble_pb2.UDPTunnel: 1,
    mumble_pb2.Authenticate: 2,
    mumble_pb2.Ping: 3,
    mumble_pb2.Reject: 4,
    mumble_pb2.ServerSync: 5,
    mumble_pb2.ChannelRemove: 6,
    mumble_pb2.ChannelState: 7,
    mumble_pb2.UserRemove: 8,
    mumble_pb2.UserState: 9,
    mumble_pb2.BanList: 10,
    mumble_pb2.TextMessage: 11,
    mumble_pb2.PermissionDenied: 12,
    mumble_pb2.ACL: 13,
    mumble_pb2.QueryUsers: 14,
    mumble_pb2.CryptSetup: 15,
    mumble_pb2.ContextActionModify: 16,
    mumble_pb2.ContextAction: 17,
    mumble_pb2.UserList: 18,
    mumble_pb2.VoiceTarget: 19,
    mumble_pb2.PermissionQuery: 20,
    mumble_pb2.CodecVersion: 21,
    mumble_pb2.UserStats: 22,
    mumble_pb2.SuggestConfig: 23,
    mumble_pb2.RequestBlob: 24
}
TYPE_MESSAGE_LOOKUP = dict((v,k) for k, v in MESSAGE_TYPE_LOOKUP.iteritems())

def serialize_(msg):
  sz = msg.SerializeToString()
  return (struct.pack(HEADER_FORMAT, MESSAGE_TYPE_LOOKUP[type(msg)], len(sz))
          + sz)


# Protobuf Builders.
def version(os = platform.system(), name = ""):
  msg = mumble_pb2.Version()
  msg.release = "1.2.2"
  msg.version = 66050
  msg.os = os
  msg.os_version = name
  return serialize_(msg)

def authenticate(username, password = None, tokens = None, celt_versions = None,
                 opus = False):
  msg = mumble_pb2.Authenticate()
  msg.username = username
  if password: msg.password = password
  if tokens: msg.tokens = tokens
  if celt_versions: msg.celt_versions = celt_versions
  if opus: msg.opus = msg.opus
  return serialize_(msg)

# Analyze Packets.
def packet_length(header):
  return struct.unpack(HEADER_FORMAT, header)[1]

def parse(header, msg):
  msgType, length = struct.unpack(HEADER_FORMAT, header)
  msgClass = TYPE_MESSAGE_LOOKUP[msgType]
  message = msgClass()
  message.ParseFromString(msg)
  return message

