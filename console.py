#!/bin/python
import logging
import sys
import threading
import time

import bots
import mumble

def main(argv):
  # logging.basicConfig(format = '%(asctime)s<%(module)s> %(message)s')
  c = bots.InteractiveBot()
  c.interact()

if __name__ == '__main__':
  main(sys.argv)
