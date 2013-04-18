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
    self.next_ping = None
    self.last_ping = None
    self.is_pinging = False
    self.mutex = thread.allocate_lock()

    threading.Thread.__init__(self)
    self.socket = self.server.connect()
    self.name = version
    self.password = None
    self.start()

  def stop(self):
    self.keep_going = False

  def ping(self):
    self.mutex.acquire()
    try:
      if self.is_pinging:
        return
      self.is_pinging = True
      self.last_ping = int(time.time() * 1000.0)
    finally:
      self.mutex.release()
    self._send(protocol.ping(int(self.last_ping)))

  def send_message(self, message, destination = None):
    self._send(protocol.text_message(session = [destination],
                                     message = message))

  def ask_texture_for_user(self, session_id):
    self._send(protocol.request_blob([sessions_id], None, None))
  def ask_comment_for_user(self, session_id):
    self._send(protocol.request_blob(None, [session_id], None))
  def ask_description_for_channel(self, channel_id):
    self._send(protocol.request_blob(None, None, [channel_id]))
  def ask_stats_for_user(self, session_id):
    self._send(protocol.user_stats(session_id))

  ##############################################################################
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

  def _recv(self):
    # Get the header first.
    try:
      header = ''
      while len(header) < protocol.HEADER_SIZE:
        received = self.socket.recv(protocol.HEADER_SIZE - len(header))
        header += received
        if len(received) == 0:
          return None
    except:
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

  # Call a delegate method named 'attr' with the args in kwargs.
  def _call(self, attr, *kargs):
    if self.delegate:
      func = getattr(self.delegate, attr, None)
      if func:
        func(*kargs)

  # Call a delegate method named 'attr' for all messages in the
  # voice packet.
  def _call_voice(self, attr, session, sequence, msg):
    pos = 0
    while ord(msg[pos]) & 0b10000000 != 0:
      sz = ord(msg[pos]) & 0b01111111
      self._call(attr, session, sequence, msg[pos:pos + sz])
      pos += sz
    else:
      sz = ord(msg[pos])
      self._call(attr, session, sequence, msg[pos:pos + sz])

  ##############################################################################
  # The different message handlers. These delegate for handling it.
  def _on_version(self, msg):
    # Handshake
    self._send(protocol.version(self.name))
    # Continue the handshake
    self._send(protocol.authenticate(self.nickname, self.password))
    # Callback at the end.
    self._call("on_version", msg)

  def _on_udp_tunnel(self, msg):
    if not self.delegate:
      return
    # This is voice data.
    type, target, session, sequence, length = (
        protocol.parse_voice_header(msg.packet))
    if type == 1:
      # Session is the timestamp.
      self._call("on_voice_ping", session)
    else:
      # For each frame, send the frame as is.
      if target == 0:
        self._call_voice("on_voice_talk", session, sequence,
                         msg.packet[length:])
      elif target == 1:
        self._call_voice("on_voice_whisper_chan", session, sequence,
                         msg.packet[length:])
      elif target == 2:
        self._call_voice("on_voice_whisper_self", session, sequence,
                         msg.packet[length:])
      # We can safely ignore the other targets, they are client -> server.

  def _on_authenticate(self, msg):
    LOGGER.error("Server should NEVER send Authenticate packets.")
    pass

  def _on_ping(self, msg):
    rtt = -1
    self.mutex.acquire()
    try:
      self.is_pinging = False
      if self.last_ping != msg.timestamp:
        LOGGER.warning(
            "Last ping (%d) time didn't correspond to expected time (%d)."
            % (msg.timestamp, self.last_ping))
      # Force a ping every 10 seconds (more than enough).
      rtt = time.time() * 1000.0 - msg.timestamp
      self.next_ping = time.time() + 10
    finally:
      self.mutex.release()
    self._call("on_pingback", rtt, msg)

  def _on_reject(self, msg):
    self._call("on_reject", msg)

  def _on_server_config(self, msg):
    self._call("on_server_config", msg)

  def _on_server_sync(self, msg):
    self._call("on_server_sync", msg)

  def _on_channel_state(self, msg):
    self._call("on_channel_state", msg)

  def _on_user_state(self, msg):
    self._call("on_user_state", msg)

  def _on_text_message(self, msg):
    self._call("on_text_message", msg)

  def _on_crypt_setup(self, msg):
    self._call("on_crypt_setup", msg)
    # Start pinging.
    self.ping()

  def _on_user_stats(self, msg):
    self._call("on_user_stats", msg)

  def _on_unknown(self, msg):
    self._call("on_unknown", type(msg), msg)

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
      mumble_pb2.UserState: self._on_user_state,
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
      mumble_pb2.UserStats: self._on_user_stats,
      # mumble_pb2.SuggestConfig: self._on_suggest_config,
      # mumble_pb2.RequestBlob: self._on_request_blob,
    }.get(type(msg), self._on_unknown)(msg)

  def _loop(self):
    fd = self.socket.fileno()
    while self.keep_going:
      # Read...
      try:
        r, _, err = select.select([fd], [], [fd], 0.3)
      except socket.error as msg:
        self._call("on_socket_exception", msg)
        self.stop()
        return False
      for n in err:
        if n == fd:
          self._call("on_socket_error")
          self.stop()
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
    return True

  def run(self):
    self._loop()
    self.socket.close()
