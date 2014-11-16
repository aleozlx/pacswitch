import random,struct,heapq,time
from twisted.internet import protocol, reactor
from twisted.python import log
from twisted.python.logfile import DailyLogFile

udpstreams=dict()

def udpGC():
	t_now=time.time()
	# log.msg('udpGC tick '+str(t_now)+' '+str([(key,udpstreams[key][1]) for key in udpstreams]))
	for k in [key for key in udpstreams if t_now-udpstreams[key][1] > 45.0]:
		# log.msg('udpGC '+str(k))
		del udpstreams[k]
	reactor.callLater(60,udpGC) 

class UDPSwitch(protocol.DatagramProtocol):
	def startProtocol(self):
		self.__agingtable=dict()

	def datagramReceived(self, data, ep):
		host, port = ep
		if len(data)<=16: 
			if ep in self.__agingtable:
				self.assignIndex(ep, self.__agingtable[ep][0])
			else:
				index=(i for i in UDPSwitch.indices() if i not in udpstreams).next()
				self.__agingtable[ep]=(index,time.time())
				udpstreams[index]=(ep,time.time())
				self.assignIndex(ep, index)
				while len(self.__agingtable)>20:
					items=[(self.__agingtable[key][1],key) for key in self.__agingtable]
					heapq.heapify(items)
					key_m=items[0][1]
					try: del self.__agingtable[key_m]
					except: pass
		else:
			try:
				to=struct.unpack('>l',data[16:20])[0]
				ep2=udpstreams[to][0]
				udpstreams[to]=(ep2,time.time())
				self.transport.write(data,ep2)
			except Exception, e:
				pass
				# log.msg('Transmission error')

	def assignIndex(self, endpoint, index):
		try: self.transport.write(struct.pack('>l', index), endpoint)
		except: log.msg('assignIndex error')

	@staticmethod
	def indices():
		yield random.randint(0,65535)

if __name__ == '__main__':
	log.startLogging(DailyLogFile.fromFullPath('/home/alex/bin/udpswitch.log'), setStdout=False)
	reactor.listenUDP(3513, UDPSwitch())
	reactor.callLater(60,udpGC) 
	reactor.run()

