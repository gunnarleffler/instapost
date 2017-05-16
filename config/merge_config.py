#!/usr/local/bin/python
helpstr = '''
merge yaml config v1.0.0
'''

import sys, os, datetime, requests, re, random, argparse, sqlite3, yaml
import dateutil.parser as dateparser

def merge(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
              sys.stderr.write('Conflict at %s \n' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def loadConfig(path):
  cfg = {}
  if args.verbose:
    sys.stderr.write(" %d entries found.\n" % (len(output)))
  infile = open(path)
  raw = []
  count = 0
  for line in infile:
    if line.strip() == "---":
      if raw != []:
        cfg = merge(cfg, yaml.safe_load("".join(raw)))
      raw = []
      count += 1
      sys.stderr.write(str(count))
    else:
      raw.append(line)
  return cfg

# main()
#--------------------------------------------------------------------------------
p = argparse.ArgumentParser(
    description=helpstr, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('-v', '--verbose', action='store_true', help='Work verbosely')
p.add_argument('-f', '--filename', help='Input filename')
args = p.parse_args()

if __name__ == "__main__":
   if args.filename:
     cfg = loadConfig(args.filename)
     print yaml.safe_dump(cfg, default_flow_style=False) 

# vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2
