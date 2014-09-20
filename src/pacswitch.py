#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Pacswitch Server. June 2014 (C) Alex
A generic data switch server using keep-alive connection,
gets over NAT and connects various kinds of clients. 

Fork me on GitHub! https://github.com/aleozlx/pacswitch

Configuration:
See options section.

Dependencies:
- Mysql connector
- twisted
"""

# standard library
import re,types,time,functools,random,struct,heapq
from time import time as timemark

# mysql
import mysql.connector

# twisted
from twisted.python import log
from twisted.python.logfile import DailyLogFile
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import protocol, reactor

# pacswitch protocol constants
PACKAGE_START  =  "\x05ALXPACSVR"
PACKAGE_END    =  "\x17CESTFINI\x04"

# options
ENABLE_LOGFILE = True
ENABLE_TERMINAL_EVENT_FEED = True
LOGFILE_FULLPATH = 'your file path for logfile'
ADMIN_KEY = 'your admin password to server via telnet'
getConnection=lambda:mysql.connector.connect(host='your host ip addr',user='your db username', password='your db password',database='pacswitch')

def debug(msg,system='pacswitch'): 
	"""Logging and debugging messages come here. 
	msg should be some function or lambda expression
	that construct the message for lazy-initialization."""
	if ENABLE_LOGFILE or ENABLE_TERMINAL_EVENT_FEED: strmsg=msg()
	if ENABLE_LOGFILE: log.msg(strmsg,system=system)
	if ENABLE_TERMINAL_EVENT_FEED:
		for s in terminals:
			try: s.sendLine('{2} [{0}] {1}'.format(system,strmsg,int(timemark())))
			except: pass

# database infrastructure
# ===========================================
"""CREATE TABLE `user` (
  `userid` VARCHAR(255) PRIMARY KEY NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `pointer` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

class mycnx:
	def __enter__(self):
		self.conn=getConnection()
		self.conn.mycur=None
		self.conn.autocommit=True
		return self.conn
	def __exit__(self, type, value, traceback):
		"""type: exc, type value: err msb, traceback: exc traceback"""
		self.conn.close()
def myexec(conn,stmt,dat):
	if conn.mycur==None: conn.mycur=conn.cursor(buffered=True)
	try: 
		t1=timemark()
		conn.mycur.execute(stmt,dat)
		debug(lambda:'raw ({0}ms) '.format(round((timemark()-t1)*1000,2))+(stmt%dat if dat else stmt),'mysql')
	except Exception,e: 
		debug(lambda:str(e),'mysql')
		return False
	else: return True	
def myquery(conn,stmt,dat): 
	return [i for i in conn.mycur] if myexec(conn,stmt,dat) else []
def myqueryone(conn,stmt,dat): 
	q=myquery(conn,stmt,dat)
	return q[0] if len(q)>=1 else None
def mydml(conn,stmt,dat): return myexec(conn,stmt,dat)
def ezquery(stmt,dat):
	with mycnx() as conn: return myquery(conn,stmt,dat)
def ezqueryone(stmt,dat):
	with mycnx() as conn: return myqueryone(conn,stmt,dat)
def ezdml(stmt,dat):
	with mycnx() as conn: return mydml(conn,stmt,dat)
# ===========================================

# database wrapper
class PacswitchDB(object): pass
class UserDB(PacswitchDB):
	@staticmethod
	def checkauth(userid,password): return ezqueryone("SELECT userid,pointer FROM `user` WHERE userid=%s AND password=%s",(userid,password))
	@staticmethod
	def getpointer(userid): return ezqueryone("SELECT userid,pointer FROM `user` WHERE userid=%s",(userid,))
	@staticmethod
	def setpointer(userid,pointer): return ezdml("UPDATE `user` SET pointer=%s WHERE userid=%s",(pointer,userid))
	@staticmethod
	def adduser(userid,password): return ezdml("INSERT INTO `user` VALUES(%s,%s,'')",(userid,password))
	@staticmethod
	def setpassword(userid,oldpasswd,newpasswd): return ezdml("UPDATE `user` SET password=%s WHERE userid=%s AND password=%s",(newpasswd,userid,oldpasswd))
	@staticmethod
	def getall(): return ezquery("SELECT * FROM `user`",None)

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

streams=StreamTracker()

def authenticated(method):
	@functools.wraps(method)
	def wrapper(self, arg):
		if self.auth: return method(self, arg)
	return wrapper

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
		self.binary=False
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
			q=UserDB.checkauth(userid,passwd)
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
			q=UserDB.getpointer(self.name)
			if q: 
				userid,pointer=q
				self.response('POINTER',pointer)
		else:
			pointer=ss[0]
			UserDB.setpointer(self.name,pointer)

	@authenticated
	def LOOKUP(self, line):
		ss=line.split('\x20')
		if len(ss)==1:
			q=UserDB.getpointer(ss[0].strip())
			self.easyResponse('LOOKUP',bool(q))

	def REGISTER(self, line):
		ss=line.split('\x20')
		if len(ss)==2:
			userid,password=ss[0],ss[1]
			if userid!='pacswitch': 
				self.easyResponse('REGISTER',UserDB.adduser(userid,password))

	@authenticated
	def PASSWD(self, line):
		ss=line.split('\x20')
		if len(ss)==2:
			oldpasswd,newpasswd=ss[0],ss[1]
			self.easyResponse('PASSWD',UserDB.setpassword(self.name,oldpasswd,newpasswd))

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
	# 			self.massive,self.binary=True,True
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
						debug(lambda:'Malformed request: {0}'.format(li))
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

class PacServerFactory(protocol.Factory):
	def buildProtocol(self, addr): return PacServer()

# telnet terminals
terminals=list()

class PacAdmin(LineOnlyReceiver):
	"""Telnet server for administration of pacswitch"""
	def connectionMade(self):
		self.auth=False
		terminals.append(self)

	def connectionLost(self, reason):
		terminals.remove(self)

	supported=['user','stream','exit'] # All commands supported
	pRule=re.compile(r'^(\w+)(\s+(.*)|)') # Command gramma
	def lineReceived(self, line):
		match=PacAdmin.pRule.match(line)
		if match:
			methodname=match.expand(r'\1')
			if methodname not in PacAdmin.supported: return # Make sure of safe interpretion
			args=[s.strip() for s in match.expand(r'\2').strip().split('\x20') if s]
			foo=getattr(self, methodname, None)
			if foo and type(foo) is types.MethodType: foo(args)

	def user(self,args):
		if self.auth:
			if len(args)==0:
				for userid,password,pointer in UserDB.getall():
					self.sendLine('{0}  {1}'.format(userid,pointer))
			elif len(args)==2 and args[0]=='lookup':
				userid=args[1]
				q=UserDB.getpointer(userid)
				if q: self.sendLine('{0}  {1}'.format(*q))
				else: self.sendLine('NOT FOUND')
			elif len(args)==3 and args[0]=='add':
				userid,password=args[1],args[2]
				UserDB.adduser(userid,password)
		elif len(args)==1 and args[0]==ADMIN_KEY: self.auth=True

	def exit(self,args):
		self.transport.loseConnection()

	@authenticated
	def stream(self,args):
		"""Inspection of stream tracker"""
		if len(args)==1 and args[0]=='show':
			smap=streams.asDict()
			for sn in smap: 
				self.sendLine('{0} -> {1}'.format(sn,'\x20'.join('#'+str(s.fileno()) for s in smap[sn])))
			self.sendLine('{0} stream(s) active.'.format(streams.totalStreams()))
		elif len(args)==2 and args[0]=='kill':
			try:
				fileno=int(args[1])
				smap=streams.asDict()
				for sn in smap: 
					for s in smap[sn]:
						if s.fileno()==fileno:
							s.loseConnection()
							smap[sn].remove(s) 
							self.sendLine('Done')
							return
			except: self.sendLine('Failed')

class PacAdminFactory(protocol.Factory):
	def buildProtocol(self, addr): return PacAdmin()

# class P2pDataSwitch(protocol.DatagramProtocol):
# 	def datagramReceived(self, data, (host, port)):
# 		if data.startswith('+'):
# 			user,addr=data.lstrip('+').split('@')
# 			mycrew[user]=Member(addr)

if __name__ == '__main__':
	if ENABLE_LOGFILE: log.startLogging(DailyLogFile.fromFullPath(LOGFILE_FULLPATH),setStdout=False)
	# reactor.listenUDP(3513, P2pDataSwitch())
	reactor.listenTCP(3512, PacServerFactory()) # Message port
	reactor.listenTCP(3511, PacAdminFactory()) # Admin port
	reactor.run()
