# class P2pDataSwitch(protocol.DatagramProtocol):
# 	def datagramReceived(self, data, (host, port)):
# 		if data.startswith('+'):
# 			user,addr=data.lstrip('+').split('@')
# 			mycrew[user]=Member(addr)



if __name__ == '__main__':
	main()

