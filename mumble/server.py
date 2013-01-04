#!/bin/python

import datetime
import logging
import socket
import ssl
import struct

LOGGER = logging.getLogger(__name__)

# Keep a server's information in a nice tidy place.
# This is hardly more than that.
class Server(object):
  def __init__(self, hostname = '', port = 64738):
    self.hostname = hostname
    self.port = int(port)

  def __str__(self):
    return "%s:%d" % (self.hostname, self.port)

  def connect(self):
    sc = ssl.wrap_socket(socket.socket(type = socket.SOCK_STREAM),
                                       ssl_version = ssl.PROTOCOL_TLSv1)
    sc.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
    try:
      sc.connect((self.hostname, self.port))
    except socket.error as e:
      LOGGER.error("Couldn't connect to server")
      raise e

    sc.setblocking(0)
    return sc

  # Returns the version, number of users, the max number of users, maximum
  # bandwidth and the ping (in milliseconds).
  def ping(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1)
    buf = struct.pack(">iQ", 0, datetime.datetime.now().microsecond)
    s.sendto(buf, (self.hostname, self.port))
    try:
      data, addr = s.recvfrom(1024)
    except socket.timeout:
      LOGGER.warning("Server timed out while pinging.")
      return None

    r = struct.unpack(">bbbbQiii", data)
    version = "%d.%d.%d" % (r[0] << 32 + r[1], r[2], r[3])
    ping = (datetime.datetime.now().microsecond - r[4]) / 1000.0
    if ping < 0: ping = ping + 1000
    return (version, r[5], r[6], r[7], ping)
