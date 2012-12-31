#!/bin/python
import logging
import sys
import threading
import time

import bots
import mumble

def main(argv):
  logging.basicConfig(format='%(asctime)s %(message)s')
  s = mumble.Server('mumble.hansl.ca')

  print "Ping: " + str(s.ping())

  b = bots.EchoBot(s)
  b.connection.join()

if __name__ == '__main__':
  main(sys.argv)
