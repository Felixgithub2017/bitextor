#!/usr/bin/env python3

import os
import sys
import argparse
import Levenshtein
import re
import base64

pathname = os.path.dirname(sys.argv[0])
sys.path.append(pathname + "/../utils")
from common import open_xz_or_gzip_or_plain


# print("pathname", pathname)

def extract_urls(html_file, url_file, docs):
    with open_xz_or_gzip_or_plain(html_file) as hd:
        with open_xz_or_gzip_or_plain(url_file) as ud:
            fileid = 1
            for url in ud:
                html_content = base64.b64decode(next(hd, None)).decode("utf-8")

                links = re.findall('''href\s*=\s*['"]\s*([^'"]+)['"]''', html_content, re.S)
                rx = re.match('(https?://[^/:]+)', url)
                if rx is not None:
                    url_domain = rx.group(1)
                    urls = "".join(links).replace(url_domain, "")
                else:
                    urls = "".join(links)
                docs[fileid] = urls
                fileid += 1


oparser = argparse.ArgumentParser(
    description="Script that rescores the aligned-document candidates provided by script bitextor-idx2ridx by using "
                "the Levenshtein edit distance of the structure of the files.")
oparser.add_argument('ridx', metavar='RIDX', nargs='?',
                     help='File with extension .ridx (reverse index) from bitextor-idx2ridx (if not provided, '
                          'the script will read from the standard input)',
                     default=None)
oparser.add_argument("--html", help="File produced during pre-processing containing all HTML files in a WARC file",
                     dest="html", required=True)
oparser.add_argument("--url", help="File produced during pre-processing containing all the URLs in a WARC file",
                     dest="url", required=True)
options = oparser.parse_args()

if options.ridx is None:
    reader = sys.stdin
else:
    reader = open(options.ridx, "r")

index = {}
documents = {}
extract_urls(options.html, options.url, documents)

for i in reader:
    fields = i.strip().split("\t")
    # The document must have at least one candidate
    if len(fields) > 1:
        sys.stdout.write(str(fields[0]))
        urls_doc = documents[int(fields[0])]
        for j in range(1, len(fields)):
            candidate = fields[j]
            candidateid = int(fields[j].split(":")[0])
            urls_candidate = documents[candidateid]
            if len(urls_candidate) == 0 or len(urls_doc) == 0:
                normdist = 0.0
            else:
                dist = Levenshtein.distance(urls_doc, urls_candidate)
                normdist = dist / float(max(len(urls_doc), len(urls_candidate)))
            candidate += ":" + str(normdist)
            sys.stdout.write("\t" + candidate)
        sys.stdout.write("\n")
