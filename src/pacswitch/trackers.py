class StreamTracker(object):
	"""Keep track of every client streams as well as their clienttype.
	Basiclly, data structure here can be illustrated as follow:

	self.streams={
		'clienttype0:username0':set([stream0,stream1,...]),
		'clienttype0:username1':set([stream0,stream1,...]),
		'clienttype1:username0':set([stream0,stream1,...]),
		'clienttype1:username1':set([stream0,stream1,...]),
		...
	}

	This can be inspected via telnet protocol.
	"""
	def __init__(self):
		super(StreamTracker, self).__init__()
		self.streams=dict()
	def __setitem__(self,key,val):
		if key in self.streams: self.streams[key].add(val)
		else: self.streams[key]=set([val])
	def __delitem__(self,(key,stream)):
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
