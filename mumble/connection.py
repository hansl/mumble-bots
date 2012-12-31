#!/bin/python

from datetime import datetime
import logging
import select
import socket
import ssl
import sys
import thread
import threading
import time

import mumble_pb2
import protocol

LOGGER = logging.getLogger(__name__)

class Connection(threading.Thread):
  def __init__(self, server, nickname, password = None, version = "hBOT 0.1",
                     delegate = None):
    self.server = server
    self.delegate = delegate
    self.nickname = nickname
    self.password = password
    self.keep_going = True
    self.queue = ""
    self.next_ping = None
    self.last_ping = None
    self.mutex = thread.allocate_lock()

    threading.Thread.__init__(self)
    self.socket = self.server.connect()
    self.name = version
    self.password = None
    self.start()

  def stop(self):
    self.keep_going = False

  def ping(self):
    self.last_ping = int(time.time() * 1000.0)
    self._send(protocol.ping(int(self.last_ping)))

  def send_message(self, message, destination = None):
    self._send(protocol.text_message(session = [destination], message = message))

  # Private. Send the queue.
  def _send_queue(self):
    self.mutex.acquire()
    msg = self.queue
    self.queue = ""
    self.mutex.release()
    return self._send_blocking(msg)

  # Private.
  def _send(self, msg):
    self._send_blocking(msg)

  def _send_blocking(self, msg):
    self.mutex.acquire()
    try:
      while len(msg) > 0:
        sent = self.socket.send(msg)
        if sent <= 0:
          LOGGER.warning("Server socket error while trying to write.")
          return False
        msg = msg[sent:]
    except:
      return False
    finally:
      self.mutex.release()
    return True

  # Private.
  def _recv(self):
    # Get the header first.
    try:
      header = self.socket.recv(protocol.HEADER_SIZE)
    except:
      return None
    if len(header) == 0:
      return None

    while len(header) < protocol.HEADER_SIZE:
      received = self.socket.recv(protocol.HEADER_SIZE - len(header))
      header += received
      if len(received) == 0:
        return None

    size = protocol.packet_length(header)
    msg = ""
    while len(msg) < size:
      received = self.socket.recv(size)
      msg += received
      if len(received) == 0:
        LOGGER.warning("Server socket died while receiving.")
        return None
    return protocol.parse(header, msg)

  # Private.
  def _call(self, attr, *kargs):
    if self.delegate:
      func = getattr(self.delegate, attr)
      if func:
        func(*kargs)

  def _call_voice(self, attr, msg, session, sequence):
    pos = 0
    while ord(msg[pos]) & 0b10000000 != 0:
      sz = msg[pos] & 0b01111111
      self._call(attr, sequence, msg[pos:pos + sz])
      pos += sz
    else:
      sz = msg[pos]
      self._call(attr, sequence, msg[pos:pos + sz])

  def _on_version(self, msg):
    self._call("on_version", msg.version, msg.release, msg.os, msg.os_version)
    # Handshake
    self._send(protocol.version(self.name))
    # Continue the handshake
    self._send(protocol.authenticate(self.nickname, self.password))

  def _on_udp_tunnel(self, msg):
    if not self.delegate:
      return
    # This is voice data.
    type, target, session, sequence, length = protocol.parse_voice_header(msg)
    if type == 1:
      # Session is the timestamp.
      self._call("on_voice_ping", session)
    else:
      # For each frame, send the frame as is.
      if target == 0:
        self._call_voice("on_voice_talk", session, sequence, msg[length:])
      elif target == 1:
        self._call_voice("on_voice_whisper_chan", session, sequence,
                         msg[length:])
      elif target == 2:
        self._call_voice("on_voice_whisper_self", session, sequence,
                         msg[length:])
      # We can safely ignore the other targets, they are client -> server.

  def _on_authenticate(self, msg):
    LOGGER.error("Server should NEVER send Authenticate packets.")
    pass

  def _on_ping(self, msg):
    if self.last_ping != msg.timestamp:
      LOGGER.warning("Last ping time didn't correspond to expected time.")
    # Force a ping every 10 seconds (more than enough).
    rtt = time.time() * 1000.0 - msg.timestamp
    self.next_ping = time.time() + 10
    self._call("on_pingback", rtt, msg.good, msg.late, msg.lost,
                              msg.udp_packets, msg.udp_ping_avg,
                              msg.udp_ping_var)

  def _on_reject(self, msg):
    self._call("on_reject", msg.type, msg.reason)

  def _on_server_config(self, msg):
    # max_bandwidth is already sent through server sync.
    self._call("on_server_config", msg.welcome_text, msg.allow_html,
                                   msg.message_length, msg.image_message_length)

  def _on_server_sync(self, msg):
    self._call("on_server_sync", msg.session, msg.max_bandwidth,
                                 msg.welcome_text, msg.permissions)

  def _on_channel_state(self, msg):
    self._call("on_channel_state", msg.channel_id, msg.parent,
                                   msg.name, msg.links, msg.description,
                                   msg.temporary, msg.position)

  def _on_text_message(self, msg):
    self._call("on_text_message", msg.actor, msg.session, msg.channel_id,
                                  msg.tree_id, msg.message)

  def _on_crypt_setup(self, msg):
    self._call("on_crypt_setup", msg.key, msg.client_nonce, msg.server_nonce)
    # Start pinging.
    self.ping()

  def _on_unknown(self, msg):
    self._call("on_unknown", type(msg), str(msg))

  def _switch(self, msg):
    if msg == None:
      return
    { mumble_pb2.Version: self._on_version,
      mumble_pb2.UDPTunnel: self._on_udp_tunnel,
      mumble_pb2.Authenticate: self._on_authenticate,
      mumble_pb2.Ping: self._on_ping,
      mumble_pb2.Reject: self._on_reject,
      mumble_pb2.ServerConfig: self._on_server_config,
      mumble_pb2.ServerSync: self._on_server_sync,
      # mumble_pb2.ChannelRemove: self._on_channel_remove,
      mumble_pb2.ChannelState: self._on_channel_state,
      # mumble_pb2.UserRemove: self._on_user_remove,
      # mumble_pb2.UserState: self._on_user_state,
      # mumble_pb2.BanList: self._on_ban_list,
      mumble_pb2.TextMessage: self._on_text_message,
      # mumble_pb2.PermissionDenied: self._on_permission_denied,
      # mumble_pb2.ACL: self._on_acl,
      # mumble_pb2.QueryUsers: self._on_query_users,
      mumble_pb2.CryptSetup: self._on_crypt_setup,
      # mumble_pb2.ContextActionModify: self._on_context_action_modify,
      # mumble_pb2.ContextAction: self._on_context_action,
      # mumble_pb2.UserList: self._on_user_list,
      # mumble_pb2.VoiceTarget: self._on_voice_target,
      # mumble_pb2.PermissionQuery: self._on_permission_query,
      # mumble_pb2.CodecVersion: self._on_codec_version,
      # mumble_pb2.UserStats: self._on_user_stats,
      # mumble_pb2.SuggestConfig: self._on_suggest_config,
      # mumble_pb2.RequestBlob: self._on_request_blob,
    }.get(type(msg), self._on_unknown)(msg)

  def _loop(self):
    fd = self.socket.fileno()
    while self.keep_going:
      # Read...
      try:
        r, _, err = select.select([fd], [], [], 1)
      except:
        return False
      for n in err:
        if n == fd:
          return False
      for n in r:
        if n == fd:
          self._switch(self._recv())
      # Send a ping when needed.
      # We only refresh next_ping on ping backs. This is to make
      # sure that if the ping is lost on the way we resend it every
      # seconds.
      if self.next_ping and time.time() >= self.next_ping:
        self.ping()

  def run(self):
    self._loop()
    self.socket.close()
