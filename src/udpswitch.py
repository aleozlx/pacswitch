import re,types,time,functools,random
from twisted.internet import protocol, reactor
from twisted.python import log
from twisted.python.logfile import DailyLogFile

class StreamTracker(object):
	"""Keep track of every client streams as well as their clienttype.
	Basiclly, data structure here can be illustrated as follow:

	device: 
		default phone: phone0 
		default host: host0
		other devices: dev0 dev1 ...
			dev: phone pad laptop tablet host ...

	self.streams={
		'clienttype0:username0:dev':((host,port),access_time),
		'clienttype0:username1:dev':((host,port),access_time),
		'clienttype1:username0:dev':((host,port),access_time),
		'clienttype1:username1:dev':((host,port),access_time),
		...
	}

	Protocol:
	
	---------------
	$offset:0~127 clienttype1:username1:dev0>clienttype1:username2:dev0
	---------------
	UDP
	---------------
	IP

	This can be inspected via telnet protocol.
	"""
	def __init__(self):
		super(StreamTracker, self).__init__()
		self.streams=dict()	
	def __setitem__(self,key,val):
		if key in self.streams: self.streams[key].add(val)
		else: self.streams[key]=set([val])
	def __delitem__(self,keyandstream):
		key,stream=keyandstream
		if key in self.streams and stream in self.streams[key]: self.streams[key].remove(stream)
		if not self.streams[key]: del self.streams[key]
	def __getitem__(self,key):
		return self.streams[key] if key in self.streams else set()
	def __contains__(self,key):
		return key in self.streams
	def asDict(self):
		return self.streams
	def totalStreams(self):
		return sum(len(self.streams[sn]) for sn in self.streams)


log.startLogging(DailyLogFile.fromFullPath('/home/alex/bin/udpswitch.log')) #,setStdout=False)
reactor.listenUDP(3513, P2pDataSwitch())
reactor.run()

