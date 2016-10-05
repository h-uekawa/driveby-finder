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
import hashlib

pattern = {
	"tag": re.compile(r"<script[^>]*>[ \t\n\r]*(.*?)[ \t\n\r]*</script>", re.I|re.S),
	"comm1": re.compile(r"^[ \t]*//[^\n]*\n?", re.M),
	"comm2": re.compile(r"^[ \t]*<!--[^\n]*\n?", re.M),
	"comm3": re.compile(r"^[ \t]*-->[^\n]*\n?", re.M),
	"comm4": re.compile(r"/\*.*?\*/", re.S),
	"xml1": re.compile(r"<!\[CDATA\[", 0),
	"xml2": re.compile(r"\]\]>[ \t]*$", re.M),
}

def remove_comments(s):
	global pattern
	s = pattern["comm1"].sub("", s)
	s = pattern["comm2"].sub("", s)
	s = pattern["comm3"].sub("", s)
	s = pattern["comm4"].sub("", s)
	s = pattern["xml1"].sub("", s)
	s = pattern["xml2"].sub("", s)
	return s

def main():
	global pattern
	
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
	extracted = database.extracted
	
	rcnt,scnt = 0,0
	for res in responses.find(None,{"content":1}):
		try:
			extracted.insert_one({"_id":res["_id"]})
		except pymongo.errors.DuplicateKeyError:
			continue
		rcnt += 1
		
		for s in pattern["tag"].findall(res["content"]):
			if s == "": continue
			s = remove_comments(s)
			
			h = hashlib.md5(s.encode("latin-1")).hexdigest()
			srecord = {
				"_id": h,
				"script": s,
				"response": res["_id"],
				"next": None,
				"prev": None,
			}
			try:
				scripts.insert_one(srecord)
				scnt += 1
			except pymongo.errors.DuplicateKeyError:
				continue
			except Exception as e:
				print repr(e)
				continue
		
		print "%d responses, %d scripts\r"%(rcnt,scnt),
		sys.stdout.flush()

if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except KeyboardInterrupt:
		pass
