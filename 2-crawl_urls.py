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
import bson
import requests
import time
from datetime import datetime,timedelta
import re

def main(pattern=None):
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
	
	user_agent = config.get("crawl", "user_agent")
	host_limit_miuntes = int(config.get("crawl", "host_limit_miuntes"))
	timeout = int(config.get("crawl", "timeout"))
	
	# url filter
	if pattern is None:
		pattern = r"http://[^/]{10,}.*(?:/|\.html)(?:\?|$)"
	
	hostlimit = {}
	
	while True:
		cur = urls.find({"response":None},sort=[("$natural",pymongo.DESCENDING)])
		if cur.count() == 0:
			time.sleep(1)
			continue
		
		for urecord in cur:
			try:
				host = urecord["url"].split("/")[2]
			except:
				continue
			if host in hostlimit and hostlimit[host] > datetime.now():
				continue
			if re.match(pattern, urecord["url"]):
				hostlimit[host] = datetime.now() + timedelta(minutes=host_limit_miuntes)
				break
		else:
			continue
		
		uid = urecord["_id"]
		url = urecord["url"]
		print repr(url)
		
		date = datetime.now()
		try:
			res = requests.get(url, timeout=timeout, headers={
				"User-Agent": user_agent,
			})
		except requests.ConnectionError:
			continue
		except requests.ReadTimeout:
			continue
		except requests.exceptions.MissingSchema:
			continue
		except UnicodeDecodeError:
			continue
		except KeyboardInterrupt:
			break
		except Exception as e:
			print repr(e)
			continue
		
		try:
			rrecord = {
				"url": url,
				"date": date,
				"status": res.status_code,
				"headers": res.headers,
				"content": res.content.decode("latin-1"), # as byte string
			}
		except bson.InvalidStringData: # UTF-8 in headers
			continue
		except bson.InvalidDocument:
			continue
		except KeyboardInterrupt:
			break
		except Exception as e:
			print repr(e)
			continue
		
		try:
			rid = responses.insert_one(rrecord).inserted_id
		except KeyboardInterrupt:
			break
		except Exception as e:
			print repr(e)
			continue
		
		urls.find_one_and_update({'_id':uid}, {'$set':{'response':rid}})

if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except KeyboardInterrupt:
		pass
