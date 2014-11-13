# class P2pDataSwitch(protocol.DatagramProtocol):
# 	def datagramReceived(self, data, (host, port)):
# 		if data.startswith('+'):
# 			user,addr=data.lstrip('+').split('@')
# 			mycrew[user]=Member(addr)

import pacswitch

# options
ENABLE_LOGFILE = True
ENABLE_TERMINAL_EVENT_FEED = True
# LOGFILE_FULLPATH = 'your file path for logfile'
# ADMIN_KEY = 'your admin password to server via telnet'
# getConnection=lambda:mysql.connector.connect(
# 	host='your host ip addr',
# 	user='your db username', 
# 	password='your db password',
# 	database='pacswitch'
# )

if __name__ == '__main__':
	pacswitch.server.run(
		ENABLE_LOGFILE = True,
		ENABLE_TERMINAL_EVENT_FEED = True,
		LOGFILE_FULLPATH = '/home/alex/pacswitch',
		ADMIN_KEY = '0000',
		getConnection = lambda:mysql.connector.connect(
			host='222.69.93.107',
			user='iadmin', 
			password='#021317',
			database='pacswitch'
		)
	)

