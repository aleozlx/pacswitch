pacswitch
=========

Pacswitch Server. June 2014 (C) Alex
A generic data switch server using keep-alive connection,
gets over NAT and connects various kinds of clients, only
requiring your account to access. 

Fork me on GitHub! https://github.com/aleozlx/pacswitch

# Features:
- Processing bandwidth about 30MB/s [lo interface speed test]
- Simple protocol that only takes about 50 lines to implement a client with C language.
- C/Java API provided.
- Multiple kinds of clients, multiple logins with same account.
- Telnet administration.

# Getting Started
You need a server that runs python interpretor and twisted and
Mysql. Then you setup a data table to store user accounts.
After that, configure pacswitch following instructions
listed in Configuration section at very beginning of
src/pacswitch.py. Last, get your brand new pacswitch 
server running.

Now that you've got it running, no matter Android SDK or 
OpenGL with which you are working, continue reading about our 
Client API usage.

# Client API
After you have a handy pacswitch server. Here's how to build a
client with our API.

- Download or fork this repository.
- Copy API into your project.
- Initiate a connection.
- Bind pacOnDataReceived method.
- Start an event loop.
- If you are not familiar with stuff, see Example section and example/
for example.

## C Language for instance
API

	bin/libpacswitchcli.a
	src/client api/pacswitchcli.h

Steps

1. Call "pacInit" to initiate a connection.
2. Call "pacOnDataReceived" to bind a handler.
3. Create subprocess or another thread for the event loop.
4. Call "pacLoop" to start an event loop.
5. Call "pacSendData" whenever you like to send data.
6. Call "pacClose" to socket.
7. Compile with "gcc -O2 -Wall -Wno-unused-result -o yourclient yourclient.c libpacswitchcli.a"

# Documentation
see doc/

# Example (from low level to high level)

## C Example (Chatting client)

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

## Java Example (Chatting client)

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

			cli.start(); //Start event loop

			Scanner scanner = new Scanner(System.in);
			try{
				while(true){ 
					String s=scanner.nextLine();
					//Send data
					try{ cli.pacSendData(s.getBytes(ENC),recv); }
					catch(UnsupportedEncodingException e){ }
				}
			}
			catch(NoSuchElementException eeof){ /* Raised because of EOF */ }
			//Close connection
			finally{ cli.close(); }
		}
	}

## Java Example (Another chatting client with higher level API)

	package com.aleozlx;
	import com.aleozlx.pacswitch.*;

	public class Messager extends PacswitchMessager {
		public static void main(String[] args) {
			Messager m=new Messager();
			if(m.connect("public","public")&&m.isAuthenticated()){
				try{ 
					/*Calling `send` here will invoke `handleMessage` method
					on the other side, and this returns the same String 
					`handleMessage` remotely returns.*/
					System.out.println(m.send("public","Hello world!")); 

				}
				catch(PacswitchException e){ e.printStackTrace(); }
				finally{ m.close(); }
			}
			else System.out.println("Network error");
		}

		public boolean connect(String userid,String password){
			return super.connect(userid,password,null,"222.69.93.107","messager1.0");
		}

		@Override
		public String handleMessage(String from, String message){
			System.out.println(String.format("%1$s: %2$s",from,message));
			return "ACK";
		}
	}


# Server Dependencies:
- Mysql connector
- twisted


