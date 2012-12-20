#!/bin/python

import logging
import socket
import ssl

# Keep a server's information in a nice tidy place.
# This is hardly more than that.
class Server(object):
  def __init__(self, hostname = '', port = 64738):
    self.hostname = hostname
    self.port = port
    self.logger = logging.getLogger(self.__class__.__name__)

  def connect(self):
    sc = ssl.wrap_socket(socket.socket(type = socket.SOCK_STREAM),
                                       ssl_version = ssl.PROTOCOL_TLSv1)
    sc.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
    try:
        sc.connect((self.hostname, self.port))
    except socket.error as e:
        self.logger.error("Couldn't connect to server")
        raise e

    return sc
