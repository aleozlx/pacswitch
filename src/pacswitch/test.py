import unittest, socket, random
from contextlib import nested
from server import PACKAGE_START, PACKAGE_END

t0 = 'PACSWITCH_TEST_T0'
t1 = 'PACSWITCH_TEST_T1'
t2 = 'PACSWITCH_TEST_T2'

class Client(object):
	def __init__(self,user=''):
		super(Client, self).__init__()
		self.user=user

	def __enter__(self):
		self.socket=self.newSocket()
		if self.user: self.loginAs(self.user)
		return self

	def __exit__(self, type, value, traceback):
		self.socket.close()

	def newSocket(self):
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('localhost',3512))
		self.send=s.send
		return s

	def loginAs(self,tu,passwd=None):
		if passwd==None: passwd=tu
		self.send(self.call('AUTH',tu,passwd))
		return self.receive()==self.easyResponse('LOGIN',True)

	def call(self,*strs):
		return ''.join([PACKAGE_START,'\x02(TXTPAC)\n','\x20'.join(strs),PACKAGE_END])

	def data(self,recv,dat):
		return ''.join([PACKAGE_START,recv,'\n',dat,PACKAGE_END])

	def relay(self,recv,dat):
		return ''.join([PACKAGE_START,recv,'>\x20',dat,PACKAGE_END])

	def easyResponse(self, title, q):
		return self.response(title,'OK' if q else 'Failed')

	def response(self, title, msg):
		return ''.join([PACKAGE_START,'pacswitch>\x20',title,':\x20',msg,PACKAGE_END])

	def receive(self):
		return self.socket.recv(4096)

class TestProtocol(unittest.TestCase, Client):
	keys=[chr(i) for i in xrange(256)]

	def newPayload(self,length):
		return ''.join(random.choice(TestProtocol.keys) for i in xrange(length))

	def setUp(self):
		self.socket = self.newSocket()

	def tearDown(self):
		self.socket.close()
		del self.send

	def test_00REGISTER(self):
		self.send(self.call('REGISTER',t0,t0))
		self.assertTrue(self.receive().startswith(PACKAGE_START))
		self.send(self.call('REGISTER',t1,t1))
		self.assertTrue(self.receive().startswith(PACKAGE_START))
		self.send(self.call('REGISTER',t2,t2))
		self.assertTrue(self.receive().startswith(PACKAGE_START))

	def test_01AUTH(self):
		self.send(self.call('AUTH',t0,t0))
		self.assertEqual(self.receive(),self.easyResponse('LOGIN',True))

	def test_01AUTH_FALSE(self):
		self.send(self.call('AUTH','\x03\x03\x03\x03\x03','000000'))
		self.assertEqual(self.receive(),self.easyResponse('LOGIN',False))

	def test_10TEST(self):
		if self.loginAs(t0):
			self.send(self.call('TEST'))
			self.assertEqual(self.receive(), self.easyResponse('TEST',True))

	def test_11LOOKUP(self):
		if self.loginAs(t0):
			self.send(self.call('LOOKUP',t0))
			self.assertEqual(self.receive(), self.easyResponse('LOOKUP',True))
			self.send(self.call('LOOKUP',t1))
			self.assertEqual(self.receive(), self.easyResponse('LOOKUP',True))
			self.send(self.call('LOOKUP',t2))
			self.assertEqual(self.receive(), self.easyResponse('LOOKUP',True))

	def test_20T_LOOPBACK(self):
		if self.loginAs(t0):
			for length in [16,64,256,1024,2048]:
				payload=self.newPayload(length)
				self.send(self.data(t0,payload))
				self.assertEqual(self.receive(),self.relay(t0,payload))

	def test_21T_ONE_TO_ONE(self):
		if self.loginAs(t0):
			with Client(t1) as c1:
				for length in [16,64,256,1024,2048]:
					payload=self.newPayload(length)
					self.send(self.data(t1,payload))
					self.assertEqual(c1.receive(),self.relay(t0,payload))

	def test_22T_ONE_TO_MANY(self):
		if self.loginAs(t0):
			with nested(Client(t1),Client(t1)) as (c1,c2):
				for length in [16,64,256,1024,2048]:
					payload=self.newPayload(length)
					self.send(self.data(t1,payload))
					self.assertEqual(c1.receive(),self.relay(t0,payload))
					self.assertEqual(c2.receive(),self.relay(t0,payload))

	def test_23T_MANY_TO_MANY(self):
		if self.loginAs(t0):
			with nested(Client(t1),Client(t1),Client(t2),Client(t2),Client(t2)) as (c11,c12,c21,c22,c23):
				for length in [16,64,256,1024,2048]:
					payload=self.newPayload(length)
					self.send(self.data(t1,payload))
					self.assertEqual(c11.receive(),self.relay(t0,payload))
					self.send(self.data(t2,payload))
					self.assertEqual(c12.receive(),self.relay(t0,payload))
					self.assertEqual(c21.receive(),self.relay(t0,payload))
					self.assertEqual(c22.receive(),self.relay(t0,payload))
					self.assertEqual(c23.receive(),self.relay(t0,payload))
					c11.send(self.data(t2,payload))
					self.assertEqual(c21.receive(),self.relay(t1,payload))
					self.assertEqual(c22.receive(),self.relay(t1,payload))
					self.assertEqual(c23.receive(),self.relay(t1,payload))
		
	def test_89PASSWD(self):
		if self.loginAs(t0):
			self.send(self.call('PASSWD',t0,t0+'_'))
			self.assertEqual(self.receive(), self.easyResponse('PASSWD',True))

	def test_89PASSWD_LOGIN(self):
		if self.loginAs(t0,t0+'_'):
			self.send(self.call('PASSWD',t0+'_',t0))
			self.assertEqual(self.receive(), self.easyResponse('PASSWD',True))
		else: self.assertTrue(False)

	def test_90REMOVE0(self):
		if self.loginAs(t0):
			self.send(self.call('REMOVE'))
			self.assertEqual(self.receive(), self.easyResponse('REMOVE',True))

	def test_90REMOVE1(self):
		if self.loginAs(t1):
			self.send(self.call('REMOVE'))
			self.assertEqual(self.receive(), self.easyResponse('REMOVE',True))

	def test_90REMOVE2(self):
		if self.loginAs(t2):
			self.send(self.call('REMOVE'))
			self.assertEqual(self.receive(), self.easyResponse('REMOVE',True))

"""
TODO:
1. flowmeter/performance monitor
2. Admin site
	http://blog.csdn.net/raptor/article/details/5602878
3. remove unnecessary logs, server members
"""

if __name__ == '__main__':
	unittest.main()
