PACKAGE_START  =  "\x05ALXPACSVR"
PACKAGE_END    =  "\x17CESTFINI\x04"

recvBuffer=''

f = open(r"pacgen.bin", "rb")

pac_count=0

while 1:
	while len(recvBuffer) and PACKAGE_START in recvBuffer and PACKAGE_END in recvBuffer:
		iI = recvBuffer.find(PACKAGE_START)
		iII = recvBuffer.find(PACKAGE_END)
		fdata = recvBuffer[iI+len(PACKAGE_START):iII]
		pac_count+=1
		recvBuffer = recvBuffer[iII+len(PACKAGE_END):]
	t=f.read(2048)
	if t:recvBuffer+=t
	else: break
	
f.close()

print pac_count

# time python pac_counter.py                                                                       18:02
# 122880
# python pac_counter.py  1.48s user 0.11s system 99% cpu 1.596 total
