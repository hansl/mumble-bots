#!/usr/bin/python
import sys

import bots
import mumble

def main(argv):
  c = bots.InteractiveBot()
  c.interact()

if __name__ == '__main__':
  main(sys.argv)
else:
  raise Exception("Importing console.py is rather useless, isn't it?")
