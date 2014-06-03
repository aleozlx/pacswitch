pacswitch
=========

Pacswitch Server. June 2014 (C) Alex
A generic data switch server using keep-alive connection,
gets over NAT and connects various kinds of clients, only
requiring your account to access. 

# Features:
- Processing bandwidth about 30MB/s [lo interface speed test]
- Simple protocol that only takes about 50 lines to implement
a client with C language.
- C/Java/Python API provided.
- Multiple kinds of clients, multiple logins with same account.
- Telnet administration.

# Client API
Documentation will come soon.

# C Example (Chatting client)

	//gcc -O2 -Wall -Wno-unused-result -o pactalk2 pactalk2.c libpacswitchcli.a
	#include <stdio.h>
	#include <stdlib.h>
	#include <string.h>
	#include <unistd.h>
	#include <sys/types.h>
	#include <signal.h>
	#include "pacswitchcli.h"

	char user[80],receiver[80],*password,outputbuffer[SZ_BUFFER];

	void OnDataReceived(char* buffer,ssize_t length){
		buffer[length]='\n';
		write(1,buffer,length+1);
	}

	int main(int argc, char const *argv[]){
		int conn; pid_t pid;

		if(argc==2)strcpy(receiver,argv[1]);
		else{
			printf("Usage: %s receiver\n",argv[0]);
			return 1;
		}

		printf("Chatting program using pacswitch protocol. May 2014 (C) Alex\n");
		printf("Name: "); scanf("%s",user);
		password = getpass("Password: ");	

		//Initialization
		conn=pacInit(user,password,receiver,"222.69.93.107","pactalk");
		free(password);
		switch(conn){
			case -1: printf("Error: socket error\n"); return 1;
			case -2: printf("Error: network error\n"); return 1;
		}

		//Bind a handler to process data
		pacOnDataReceived(OnDataReceived);

		//Fork the process
		pid=fork();
		if(pid==-1)printf("Error: cannot fork process\n");
		else if(pid==0)pacLoop(); //OnDataReceived will be called here when a packet is integrate
		else{ // tty -> socket
			while(gets(outputbuffer)){ 
				size_t outputlen=strlen(outputbuffer);
				//Send data
				if(outputlen!=0)pacSendData(outputbuffer,outputlen,receiver);
			}
			kill(pid,SIGKILL);
		}
		//Close connection
		pacClose();
		return 0;
	}

# Java Example (Chatting client)

	import com.aleozlx.pacswitch.PacswitchClient;
	import java.lang.*;
	import java.io.*;
	import java.util.*;

	public class Pactalk{
		public static final String ENC="utf-8";
		public static void main(String[] args) {
			String recv; Console io = System.console();
			if(args.length>=1)recv=args[0];
			else { System.out.println("Usage: java Pactalk receiver"); return; }
			System.out.println("Chatting program using pacswitch protocol. May 2014 (C) Alex");
			System.out.print("Name: ");
			String user=io.readLine();
			System.out.print("Password: ");
			String password=new String(io.readPassword());

			//Bind a handler to process data
			final PacswitchClient cli=new PacswitchClient(){
				@Override
				public void pacOnDataReceived(String sender,byte[] buffer){ 
					try{ 
						System.out.print(sender);
						System.out.print(": ");
						System.out.println(new String(buffer,ENC)); 
					}
					catch(UnsupportedEncodingException e){ e.printStackTrace(); }
				}
			};

			//Initialization
			if(!cli.pacInit(user,password,"222.69.93.107","pactalk")){ 
				System.out.println("Error: network error"); return; 
			}

			try{
				//The same as pacLoop(), but in asynchronous way.
				cli.pacReceiveAsync(); //pacOnDataReceived will be called here when a packet is integrate
				Scanner scanner = new Scanner(System.in);
				while(true){ 
					String s=scanner.next();
					//Send data
					try{ cli.pacSendData(s.getBytes(ENC),recv); }
					catch(UnsupportedEncodingException e){ e.printStackTrace(); }
				}
			}
			//Close connection
			finally{ cli.pacClose(); }
		}
	}

# Server Dependencies:
- Mysql connector
- twisted


