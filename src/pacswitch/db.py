import time

# database infrastructure
# ===========================================
"""CREATE TABLE `user` (
  `userid` VARCHAR(255) PRIMARY KEY,
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
		t1=time.time()
		conn.mycur.execute(stmt,dat)
		debug(lambda:'raw ({0}ms) '.format(round((time.time()-t1)*1000,2))+(stmt%dat if dat else stmt),'mysql')
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
	def deluser(userid): return ezdml("DELETE FROM `user` WHERE userid=%s",(userid,))
	@staticmethod
	def setpassword(userid,oldpasswd,newpasswd): return ezdml("UPDATE `user` SET password=%s WHERE userid=%s AND password=%s",(newpasswd,userid,oldpasswd))
	@staticmethod
	def getall(): return ezquery("SELECT * FROM `user`",None)
