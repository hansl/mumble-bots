#!/bin/python
import sys

import mumble

def main(argv):
  s = mumble.Server('mumble.hansl.ca')
  c = mumble.Connection(s, '.MyBot')
  c.start()
  c.join()

if __name__ == '__main__':
  main(sys.argv)
