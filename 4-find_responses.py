#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   driveby-finder - Scripts for MWSCup 2016
#   https://github.com/h-uekawa/driveby-finder
#
#   Copyright (c) 2016 Team Security Anthem (Okayama Univ.)
#   Released under the MIT License, see LICENSE.txt
#
##

import sys
import ConfigParser
import pymongo
import re

def main(pattern):
	# config
	config = ConfigParser.SafeConfigParser()
	config.read("./config.ini")
	
	# database
	host = config.get("mongodb", "host")
	port = int(config.get("mongodb", "port"))
	dbname = config.get("mongodb", "database")
	client = pymongo.MongoClient(host, port)
	database = client[dbname]
	
	# collections
	urls = database.urls
	responses = database.responses
	scripts = database.scripts
	
	pattern = re.compile(pattern, 0)
	
	results = responses.find({"content":pattern})
	
	for record in results:
		
		response_id = record["_id"]
		url = record["url"]
		status = record["status"]
		content = record["content"].encode("latin-1")
		
		# reduce newlines
		content = re.sub(r"(?:\r\n|\r|\n)[ \t]*(?:\r\n|\r|\n)(?:[ \t]*(?:\r\n|\r|\n))+", "\n\n", content)
		
		sys.stderr.write("// %s %s\n"%(status,url))
		print "// "+("="*77)
		print "// %s %s"%(status,url)
		print "// "+("="*77)
		print content
		print


if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except KeyboardInterrupt:
		pass
