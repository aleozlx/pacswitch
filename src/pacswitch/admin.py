import re
from utils import authenticated
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import protocol

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

class Factory(protocol.Factory):
	def buildProtocol(self, addr): return PacAdmin()

