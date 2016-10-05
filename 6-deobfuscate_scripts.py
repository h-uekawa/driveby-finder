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

def deobfuscate(s):
	
	# here deobfuscating code
	
	return s

def main(infile=None):
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
	scripts = database.scripts
	
	results = scripts.find({"next":None})
	
	scnt = 0
	for record in results:
		script_id = record["_id"]
		
		scnt += 1
		sys.stderr.write("%d %s\r"%(scnt,script_id))
		sys.stderr.flush()
		
		script = record["script"]
		script = script.encode("latin-1")
		
		newscript = deobfuscate(script)
		if newscript == script:
			continue
		
		newscript = remove_comments(newscript)
		hash = hashlib.md5(newscript).hexdigest()
		
		record["_id"] = hash
		record["script"] = newscript.decode("latin-1")
		record["prev"] = script_id
		
		print "%s -> %s"%(script_id,hash)
		try:
			scripts.find_one_and_update({"_id":script_id},{"$set":{"next":hash}})
			scripts.insert_one(record)
		except pymongo.errors.DuplicateKeyError:
			continue
		except Exception as e:
			print repr(e)
			continue

if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except KeyboardInterrupt:
		pass
