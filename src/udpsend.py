import os,threading,socket

s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.setblocking(False)
s.sendto("Hello World",("222.69.93.107",3513))

