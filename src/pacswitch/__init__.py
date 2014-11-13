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

import server

__all__=[
	'admin',
	'db',
	'server',
	'trackers',
	'utils',
]
