"""
#!/usr/bin/env python 
# -*- coding: utf-8 -*-

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

# options
ENABLE_LOGFILE = True
ENABLE_TERMINAL_EVENT_FEED = True
LOGFILE_FULLPATH = 'your file path for logfile'
ADMIN_KEY = 'your admin password to server via telnet'
getConnection=lambda:mysql.connector.connect(
	host='your host ip addr',
	user='your db username', 
	password='your db password',
	database='pacswitch'
)

__all__=['admin','db','utils','types','server']
