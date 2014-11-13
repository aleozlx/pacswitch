import functools, time

def authenticated(method):
	@functools.wraps(method)
	def wrapper(self, arg):
		if self.auth: return method(self, arg)
	return wrapper
