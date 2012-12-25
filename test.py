#!/bin/python
import logging
import sys
import time

import mumble

class TestBot(mumble.Bot):
  def __init__(self, server):
    mumble.Bot.__init__(self, server, ".Bot", "TestBot 2000")


def main(argv):
  logging.basicConfig(format='%(asctime)s %(message)s')
  s = mumble.Server('mumble.hansl.ca')

  print "Ping: " + str(s.ping())

  b = TestBot(s)
  b.connection.join()

if __name__ == '__main__':
  main(sys.argv)
