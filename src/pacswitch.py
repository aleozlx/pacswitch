#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Pacswitch Server. June 2014 (C) Alex
A generic data switch server using keep-alive connection,
gets over NAT and connects various kinds of clients, only
requiring an account to access. 

Features:
- Processing bandwidth about 30MB/s [lo interface speed test]
- Simple protocol that only takes about 50 lines to implement
a client with C language.
- C/Java/Python API provided.
- Multiple kinds of clients, multiple logins with same account.
- Telnet administration.

Dependencies:
- Mysql connector
- twisted
"""

# standard library
import re,types,time
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
LOGFILE_FULLPATH = '/home/alex/log/pacswitch'

getConnection=lambda:mysql.connector.connect(
	host='222.69.93.107',
	user='iadmin', 
	password='#021317',
	database='pacswitch'
)

def debug(msg,system='pacswitch'): 
	"""Logging and debugging messages come here. 
	msg should be some function or lambda expression
	that construct the message for lazy-initialization."""
	if ENABLE_LOGFILE or ENABLE_TERMINAL_EVENT_FEED: strmsg=msg()
	if ENABLE_LOGFILE: log.msg(strmsg,system=system)
	if ENABLE_TERMINAL_EVENT_FEED:
		for s in terminals:
			try: s.sendLine('[{0}] '.format(system),strmsg)
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
	def checkauth(userid,password): return ezqueryone("""SELECT userid,pointer FROM `user` WHERE userid=%s AND password=%s""",(userid,password))
	@staticmethod
	def getpointer(userid): return ezqueryone("""SELECT userid,pointer FROM `user` WHERE userid=%s""",(userid,))

class StreamTracker(object):
	"""Keep track of every client streams as well as their clienttype.
	Basiclly, data structure here can be illustrated as follow:

	self.streams={
		'clienttype0:username0':[stream0,stream1,...],
		'clienttype0:username1':[stream0,stream1,...],
		'clienttype1:username0':[stream0,stream1,...],
		'clienttype1:username1':[stream0,stream1,...],
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
		ss=line.split('\x20')
		userid,passwd,self.clienttype=ss[0],ss[1],(ss[2] if len(ss)>=3 else '')
		if not UserDB.checkauth(userid,passwd): 
			debug(lambda:"{0} tried to login with password '{1}' and had failed".format(userid,passwd))
			self.transport.write(''.join([PACKAGE_START,'pacswitch> Login authentication failed',PACKAGE_END]))
		else:
			self.name=userid
			self.auth=True
			streams[self.streamName]=self.transport
			debug(lambda:'{0} Online opened {1} stream(s)'.format(self.name,len(streams[self.streamName])))
			self.transport.write(''.join([PACKAGE_START,'pacswitch> Authenticated',PACKAGE_END]))

	def MASS(self, line):
		""""MASS" command: Incidates a massive data transmissioin"""
		self.massive=True

	pRule=re.compile(r'^([A-Z]+)(\s+(.*)|)') # Command gramma
	def dataReceived(self, data):
		"""Analyzes data packets and switch'em to another client"""
		self.recvBuffer += data # Accumulate data till at least one integrate packet appear
		# Buffer size limited down to 5MB to prevent server from potential attack
		if len(self.recvBuffer)>5242880: 
			self.transport.loseConnection()
			return
		while len(self.recvBuffer) and PACKAGE_START in self.recvBuffer and PACKAGE_END in self.recvBuffer:
			# [Performance Test @ Intel Core i3 Ubuntu] 
			# This is only 4.5s/GB slower than the equivalent C program, thus no boost needed
			iI = self.recvBuffer.find(PACKAGE_START)
			iII = self.recvBuffer.find(PACKAGE_END)
			fdata = self.recvBuffer[iI+len(PACKAGE_START):iII]
			self.recvBuffer = self.recvBuffer[iII+len(PACKAGE_END):]
			if fdata.startswith('\x02(TXTPAC)\n'): 
				# Text based protocol now
				for li in fdata.split('\n')[1:]:
					match=PacServer.pRule.match(li) # Make sure of safe interpretion
					try:
						methodname=match.expand(r'\1')
						if self.auth or methodname=='AUTH':
							foo=getattr(self, methodname, None)
							if foo and type(foo) is types.MethodType: foo(match.expand(r'\2').strip())
							else: raise Exception()
					except Exception, e: 
						debug(lambda:'Malformed request: {0}'.format(li))
						time.sleep(0.8)	# Control pace of potential attack	
			elif self.auth:
				# A data transmittion
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

	pRule=re.compile(r'^(\w+)(\s+(.*)|)') # Command gramma
	def lineReceived(self, line):
		match=PacAdmin.pRule.match(line)
		if match:
			methodname=match.expand(r'\1')
			if methodname not in ['user','stream','exit']: return # Make sure of safe interpretion
			args=[s.strip() for s in match.expand(r'\2').strip().split('\x20') if s]
			if self.auth or methodname=='user' or methodname=='exit':
				foo=getattr(self, methodname, None)
				if foo and type(foo) is types.MethodType: foo(args)

	def user(self,args):
		"""Authentication"""
		if len(args)==1 and args[0]=='alex0764': self.auth=True

	def exit(self,args):
		self.transport.loseConnection()

	def stream(self,args):
		"""Inspection of stream tracker"""
		if len(args)==1:
			if args[0]=='show':
				smap=streams.asDict()
				for sn in smap: 
					self.sendLine('{0} -> {1}'.format(sn,' '.join('#'+str(s.fileno()) for s in smap[sn])))
				self.sendLine('{0} stream(s) active.'.format(streams.totalStreams()))

class PacAdminFactory(protocol.Factory):
	def buildProtocol(self, addr): return PacAdmin()

if ENABLE_LOGFILE: log.startLogging(DailyLogFile.fromFullPath(LOGFILE_FULLPATH),setStdout=False)
reactor.listenTCP(3512, PacServerFactory()) # Data port
reactor.listenTCP(3511, PacAdminFactory()) # Admin port
reactor.run()