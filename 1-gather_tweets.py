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
import tweepy
import time

class StreamListener(tweepy.StreamListener):
	def __init__(self, urls):
		super(StreamListener, self).__init__()
		self.urls = urls
		urls.create_index([("url", pymongo.ASCENDING)], unique=True)
		self.unum = urls.count()
	
	def on_status(self, status):
		urls = status.entities["urls"]
		if len(urls) == 0:
			return
		
		for url in urls:
			record = {"url":url["expanded_url"],"response":None}
			try:
				self.urls.insert_one(record)
				self.unum += 1
			except pymongo.errors.DuplicateKeyError:
				pass
			except pymongo.errors.WriteError:
				pass
		
		print "%d urls \r"%(self.unum,),
		sys.stdout.flush()
	
	def on_error(self, status_code):
		pass

def main(*keywords):
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
	
	# twitter auth
	consumer_key = config.get("twitter", "consumer_key")
	consumer_secret = config.get("twitter", "consumer_secret")
	access_token_key = config.get("twitter", "access_token_key")
	access_token_secret = config.get("twitter", "access_token_secret")
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token_key, access_token_secret)
	
	api = tweepy.API(auth)
	
	listener = StreamListener(urls)
	
	stream = tweepy.Stream(auth=api.auth, listener=listener)
	
	if len(keywords) == 0:
		keywords = ["http"]
	
	while True:
		try:
			stream.filter(track=keywords)
		except KeyboardInterrupt:
			break
		except Exception as e:
			print repr(e)
			time.sleep(60)
			stream = tweepy.Stream(auth=api.auth, listener=listener)

if __name__ == "__main__":
	try:
		main(*sys.argv[1:])
	except KeyboardInterrupt:
		pass
