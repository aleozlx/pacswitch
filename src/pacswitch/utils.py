import functools

def authenticated(method):
	@functools.wraps(method)
	def wrapper(self, arg):
		if self.auth: return method(self, arg)
	return wrapper

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
