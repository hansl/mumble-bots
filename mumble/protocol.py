# Describes the protocol used to communicate with Mumble.
# This is a series of methods that creates a message to be sent directly
# to Mumble. It's stateless and is just used for convenience.
# It also prevents anyone else from dealing with the pesky Mumble
# protobufs. Instead they just need to call these methods.

import platform
import struct

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

def ping(timestamp = None):
  msg = mumble_pb2.Ping()
  if timestamp: msg.timestamp = timestamp
  return serialize_(msg)

def text_message(actor = None, session = None, channels = None, tree = None,
                 message = None):
  msg = mumble_pb2.TextMessage()
  if actor: msg.actor = actor
  if session: msg.session.extend(session)
  if channels: msg.channel_id.extend(channels)
  if tree: msg.tree_id.extend(tree)
  if message: msg.message = message
  return serialize_(msg)

def request_blob(texture = None, comment = None, description = None):
  msg = mumble_pb2.RequestBlob()
  if texture: msg.session_texture.extend(texture)
  if comment: msg.session_comment.extend(comment)
  if description: msg.channel_description.extend(description)
  return serialize_(msg)

def user_stats(session):
  msg = mumble_pb2.UserStats()
  msg.session = session
  return serialize_(msg)

# Analyze Packets.
def packet_length(header):
  return struct.unpack(HEADER_FORMAT, header)[1]

def parse(header, msg):
  msgType, length = struct.unpack(HEADER_FORMAT, header)
  msgClass = TYPE_MESSAGE_LOOKUP[msgType]
  message = msgClass()
  # UDPTunnel are not encapsulated in protobufs, but are just streamed
  # bytes.
  if msgType == 1:
    message.packet = msg
  else:
    message.ParseFromString(msg)
  return message

# Decode the session from the varint format
# (see http://mumble.sourceforge.net/Protocol)
def _decode_varint(msg):
  b0 = ord(msg[0])
  if   b0 & 0b10000000 == 0:
    # 7 bits
    return (b0 & 0b01111111, 1)
  elif b0 & 0b01000000 == 0:
    # 6 bits + 1 byte
    return ((b0 & 0b00111111 << 8) | ord(msg[1]), 2)
  elif b0 & 0b00100000 == 0:
    # 5 bits + 2 bytes
    return ((b0 & 0b00011111 << 16) | (ord(msg[1]) << 8) | ord(msg[2]), 3)
  elif b0 & 0b00010000 == 0:
    # 4 bits + 3 bytes
    return ((b0 & 0b00001111 << 24) | (ord(msg[1]) << 16) | (ord(msg[2]) << 8) |
            ord(msg[3]), 4)
  elif b0 & 0b00001100 == 0:
    # 4 bytes
    return ((ord(msg[1]) << 16) | (ord(msg[2]) << 16) | (ord(msg[3]) << 8) |
            (ord(msg[4])), 5)
  elif b0 & 0b00001100 == 1:
    # 8 bytes
    return ((ord(msg[1]) << 56) | (ord(msg[2]) << 48) | (ord(msg[3]) << 40) |
            (ord(msg[4]) << 32) | (ord(msg[5]) << 24) | (ord(msg[6]) << 16) |
            (ord(msg[7]) <<  8) |  ord(msg[8]), 9)
  elif b0 & 0b00001100 == 2:
    # Negative varint
    val, length = _decode_varint(msg[1:])
    return (-val, length + 1)
  elif b0 & 0b00001100 == 2:
    # Negative 2 bits
    return (-(b0 & 0b00000011), 1)

def parse_voice_header(msg):
  h = ord(msg[0])
  type = (h & 0b11100000) >> 5
  target = (h & 0b00011111)
  (session, session_length) = _decode_varint(msg[1:])
  if (session_length + 1 >= len(msg)):
    # Means there's no sequence number.
    sequence = 0
    sequence_length = 0
  else:
    (sequence, sequence_length) = _decode_varint(msg[session_length:])
  header_length = session_length + sequence_length
  return (type, target, session, sequence, header_length)
