import admin,db
import re,types,time,random,traceback
from utils import authenticated
from trackers import StreamTracker
from twisted.python import log
from twisted.internet import protocol, reactor

# pacswitch protocol constants
PACKAGE_START  =  "\x05ALXPACSVR"
PACKAGE_END    =  "\x17CESTFINI\x04"

# options
ENABLE_TERMINAL_EVENT_FEED = False
ENABLE_LOGFILE = False

def debug(msgf,system='pacswitch'): 
	if ENABLE_LOGFILE or ENABLE_TERMINAL_EVENT_FEED:
		strmsg=msgf()
		if ENABLE_LOGFILE: log.msg(strmsg,system=system)
		if ENABLE_TERMINAL_EVENT_FEED:
			for s in admin.terminals:
				try: s.sendLine('{2} [{0}] {1}'.format(system,strmsg,int(time.time())))
				except: pass

streams=StreamTracker()

class PacServer(protocol.Protocol,object):
	"""Pacswitch Server implementation"""
	def connectionMade(self):
		"""Initialization"""
		self._name=''
		self._clienttype=''
		self.recvBuffer=''
		self.clienttype=''
		self.streamName=''
		self.auth=False
		self.totalsize=0
		self.massive=False

	@property
	def name(self): return self._name
	@name.setter
	def name(self,value): self._name,self.streamName = value, self.getStreamName(value)
	@property
	def clienttype(self): return self._clienttype
	@clienttype.setter
	def clienttype(self,value): self._clienttype,self.streamName = value,self.getStreamName(self.name)
	def getStreamName(self,name): return '{0}:{1}'.format(self.clienttype,name)
	def updateSize(self,value):
		"""Update total size of data transmitted through this stream"""
		self.totalsize+=value
		if self.totalsize>524288: self.massive=True

	def connectionLost(self, reason):
		if self.streamName in streams: 
			debug(lambda:'{0} Offline {1}B transmitted'.format(self.name,self.totalsize))
			del streams[(self.streamName,self.transport)]

	def AUTH(self, line):
		""""AUTH" command: User Authentication"""
		if self.auth==False:
			ss=line.split('\x20')
			userid,passwd,self.clienttype=ss[0],ss[1],(ss[2] if len(ss)>=3 else '')
			q=db.UserDB.checkauth(userid,passwd)
			if q: 
				self.name=userid
				self.auth=True
				streams[self.streamName]=self.transport
				debug(lambda:'{0} Online opened {1} stream(s)'.format(self.name,len(streams[self.streamName])))
			else:
				debug(lambda:"{0} tried to login with password '{1}' and had failed".format(userid,passwd))
			self.easyResponse('LOGIN',q)

	def MASS(self, line):
		""""MASS" command: Declare a massive data transmissioin"""
		self.massive=True

	@authenticated
	def POINTER(self, line):
		ss=line.split('\x20')
		if len(ss)==0:
			q=db.UserDB.getpointer(self.name)
			if q: 
				userid,pointer=q
				self.response('POINTER',pointer)
		else:
			pointer=ss[0]
			db.UserDB.setpointer(self.name,pointer)

	@authenticated
	def LOOKUP(self, line):
		ss=line.split('\x20')
		if len(ss)==1:
			q=db.UserDB.getpointer(ss[0].strip())
			self.easyResponse('LOOKUP',bool(q))

	def REGISTER(self, line):
		ss=line.split('\x20')
		if len(ss)==2:
			userid,password=ss[0],ss[1]
			if userid!='pacswitch': 
				self.easyResponse('REGISTER',db.UserDB.adduser(userid,password))

	@authenticated
	def PASSWD(self, line):
		ss=line.split('\x20')
		if len(ss)==2:
			oldpasswd,newpasswd=ss[0],ss[1]
			self.easyResponse('PASSWD',db.UserDB.setpassword(self.name,oldpasswd,newpasswd))

	@authenticated
	def REMOVE(self, line):
		self.easyResponse('REMOVE',db.UserDB.deluser(self.name))

	@authenticated
	def TEST(self, line):
		self.easyResponse('TEST',True)

	@authenticated
	def STREAM(self, line):
		while 1:
			srcid,dstid=tuple(''.join(random.choice('qwertyuiopasdfghjklzxcvbnmzy') for i in xrange(20)) for k in xrange(2))
			if srcid not in streams and dstid not in streams: 
				streams[srcid],streams[dstid]=None,None
				# TODO expire it after 10s if unused
				break
		self.response('STREAM','\x20'.join((line.strip(),srcid,dstid)))

	# def BIN(self, line):
	# 	ss=line.split('\x20')
	# 	if len(ss)==2:
	# 		srcid,dstid=ss[0],ss[1]
	# 		if srcid in streams and streams[srcid]==None and dstid in streams:
	# 			streams[srcid]=self.transport

	def response(self, title, msg):
		self.transport.write(''.join([PACKAGE_START,'pacswitch>\x20',title,':\x20',msg,PACKAGE_END]))

	def easyResponse(self, title, q):
		self.response(title,'OK' if q else 'Failed')

	pRule=re.compile(r'^([A-Z]+)(\s+(.*)|)') # Command gramma
	def dataReceived(self, data):
		"""Analyze data packets and switch'em to another client"""
		self.recvBuffer += data # Accumulate data till at least one integrate packet appears
		# Buffer size limited down to 5MB to prevent server from potential attack
		if len(self.recvBuffer)>5242880: 
			self.transport.loseConnection()
			return
		while len(self.recvBuffer) and PACKAGE_START in self.recvBuffer and PACKAGE_END in self.recvBuffer:
			# [Performance Test @ Intel Core i3 Ubuntu] 
			# This is only 4.5s/GB slower than the equivalent C program, thus no boost needed
			iI = self.recvBuffer.find(PACKAGE_START)
			iII = self.recvBuffer.find(PACKAGE_END)
			if iII<iI: # Is this some DoS attack? PACKAGE_END is not allowed to appear in user data.
				self.recvBuffer = self.recvBuffer[iII+len(PACKAGE_END):]
				continue
			fdata = self.recvBuffer[iI+len(PACKAGE_START):iII]
			self.recvBuffer = self.recvBuffer[iII+len(PACKAGE_END):]
			if fdata.startswith('\x02(TXTPAC)\n'): 
				# Text based protocol now
				for li in fdata.split('\n')[1:]:
					match=PacServer.pRule.match(li) # Make sure of safe interpretion
					try:
						methodname=match.expand(r'\1')
						foo=getattr(self, methodname, None)
						if foo and type(foo) is types.MethodType: foo(match.expand(r'\2').strip())
						else: raise Exception()
					except Exception, e: 
						debug(lambda:'Malformed request: {0}\n{1}'.format(li,traceback.format_exc()))
						time.sleep(0.8)	# Control pace of potential attack	
			elif self.auth:
				# Packets switching
				iI = fdata.find('\n')
				name=fdata[:iI] 
				recv_streams=streams[self.getStreamName(name)] # Figure out receiver client
				if recv_streams:
					datasize=len(fdata)-iI-1
					self.updateSize(datasize)
					if not self.massive: # Keep record of the transmittion
						debug(lambda:'{0} -> {1} * {2} {3}B'.format(self.streamName,name,len(recv_streams),datasize))
					for s in recv_streams: # Broadcast down to all clients with same account same clienttype
						try: s.write(''.join([PACKAGE_START,self.name,'>\x20',fdata[iI+1:],PACKAGE_END]))
						except: debug(lambda:'Transmissioin failure')

class ServerFactory(protocol.Factory):
	def buildProtocol(self, addr): return PacServer()

def run(**options):
	if 'ENABLE_TERMINAL_EVENT_FEED' in options: 
		global ENABLE_TERMINAL_EVENT_FEED
		ENABLE_TERMINAL_EVENT_FEED=options['ENABLE_TERMINAL_EVENT_FEED']

	if 'LOGFILE_FULLPATH' in options: 
		from twisted.python.logfile import DailyLogFile
		global ENABLE_LOGFILE
		ENABLE_LOGFILE = True
		log.startLogging(
			DailyLogFile.fromFullPath(options['LOGFILE_FULLPATH']),
			setStdout=False
		)

	if 'ADMIN_KEY' in options: 
		admin.ADMIN_KEY=options['ADMIN_KEY']
		reactor.listenTCP(3511, admin.Factory())

	assert 'DB_CONNECTION' in options
	import mysql.connector
	db.getConnection=lambda:mysql.connector.connect(**options['DB_CONNECTION'])
	db.debug=debug
	admin.UserDB=db.UserDB

	# reactor.listenUDP(3513, P2pDataSwitch())
	reactor.listenTCP(3512, ServerFactory())
	reactor.run()
