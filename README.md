pacswitch
=========

Pacswitch Server. June 2014 (C) Alex
A generic data switch server using keep-alive connection,
gets over NAT and connects various kinds of clients, only
requiring an account to access. 

# Features:
- Processing bandwidth about 30MB/s [lo interface speed test]
- Simple protocol that only takes about 50 lines to implement
a client with C language.
- C/Java/Python API provided.
- Multiple kinds of clients, multiple logins with same account.
- Telnet administration.

# Dependencies:
- Mysql connector
- twisted

