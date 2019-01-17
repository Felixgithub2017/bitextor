#!/usr/bin/env python3

import os
import sys
import argparse
from operator import itemgetter
import Levenshtein
import re
import base64

pathname = os.path.dirname(sys.argv[0])
sys.path.append(pathname + "/../utils")
from common import open_xz_or_gzip_or_plain
#print("pathname", pathname)

def read_urls(f, docs):
  with open_xz_or_gzip_or_plain(f) as fd:
    fileid = 1
    for u in fd:
      u=u.strip()
      rx = re.match('(https?://[^/:]+)', u)
      if rx != None:
        url_domain = rx.group(1)
        url = u.replace(url_domain,"")
      else:
        url = u
      docs[fileid] = url
      fileid += 1

oparser = argparse.ArgumentParser(description="Script that rescores the aligned-document candidates provided by script bitextor-idx2ridx by using the Levenshtein edit distance of the structure of the files.")
oparser.add_argument('ridx', metavar='RIDX', nargs='?', help='File with extension .ridx (reverse index) from bitextor-idx2ridx (if not provided, the script will read from the standard input)', default=None)
oparser.add_argument("--url", help="File produced during pre-processing containing all the URLs in a WARC file", dest="url", required=True)
options = oparser.parse_args()

if options.ridx == None:
  reader = sys.stdin
else:
  reader = open(options.ridx,"r")

index = {}
documents = {}
read_urls(options.url, documents)

for i in reader:
  fields = i.strip().split("\t")
  #The document must have at least one candidate
  if len(fields)>1:
    sys.stdout.write(str(fields[0]))
    url_doc=documents[int(fields[0])]
    for j in range(1,len(fields)):
      candidate = fields[j]
      candidateid = int(fields[j].split(":")[0])
      url_candidate=documents[candidateid]
      if len(url_candidate) == 0 or len(url_doc) == 0:
        normdist = 0.0
      else:
        dist = Levenshtein.distance(url_doc,url_candidate)
        normdist=dist/float(max(len(url_doc),len(url_candidate)))
      candidate+=":"+str(normdist)
      sys.stdout.write("\t"+candidate)
    sys.stdout.write("\n")
