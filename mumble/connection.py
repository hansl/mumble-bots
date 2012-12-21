#!/bin/python

import logging
import socket
import ssl
import sys
import thread
import threading

import protocol

class Connection(threading.Thread):
  def __init__(self, server, nickname, password = None, delegate = None):
    self.socket = server.connect()
    self.logger = logging.getLogger(self.__class__.__name__)
    self.mutex  = thread.allocate_lock()
    self.delegate = delegate

    self.send_(protocol.version(name = "hBOT 0.1") +
               protocol.authenticate(nickname, password))
    threading.Thread.__init__(self)

  # Private.
  def send_(self, msg):
    self.mutex.acquire()
    try:
      while len(msg) > 0:
        sent = self.socket.send(msg)
        if sent < 0:
          self.logger.warning("Server socket error while trying to write.")
          return False
        msg = msg[sent:]
    finally:
      self.mutex.release()
    return True

  # Private.
  def recv_(self):
    # Get the header first.
    header = self.socket.recv(protocol.HEADER_SIZE)

    size = protocol.packet_length(header)
    msg = ""
    while len(msg) < size:
      received = self.socket.recv(size)
      msg += received
      if len(received) == 0:
        self.logger.warning("Server socket died while receiving.")
    return protocol.parse(header, msg)

  def run(self):
    while True:
      msg = self.recv_()  # Blocking.
      print str(type(msg)), msg

