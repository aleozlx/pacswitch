import pacswitch

if __name__ == '__main__':
	# pacswitch.server.run(
	# 	LOGFILE_FULLPATH = 'your file path for logfile',
	# 	ADMIN_KEY = '0000',
	# 	DB_CONNECTION = dict(
	# 		host = 'localhost',
	# 		user = 'admin', 
	# 		password = 'admin',
	# 		database = 'pacswitch'
	# 	)
	# )

	pacswitch.server.run(
		LOGFILE_FULLPATH = '/home/alex/pacswitch',
		ADMIN_KEY = '0000',
		DB_CONNECTION = dict(
			host = '222.69.93.107',
			user = 'iadmin', 
			password = '#021317',
			database = 'pacswitch'
		)
	)

