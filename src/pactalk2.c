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

	conn=pacInit(user,password,receiver,"222.69.93.107","pactalk");
	free(password);
	switch(conn){
		case -1: printf("Error: socket error\n"); return 1;
		case -2: printf("Error: network error\n"); return 1;
	}
	pacOnDataReceived(OnDataReceived);

	pid=fork();
	if(pid==-1)printf("Error: cannot fork process\n");
	else if(pid==0)pacLoop();
	else{ // tty -> socket
		while(gets(outputbuffer)){ 
			size_t outputlen=strlen(outputbuffer);
			if(outputlen!=0)pacSendData(outputbuffer,outputlen,receiver);
		}
		kill(pid,SIGKILL);
	}
	pacClose();
	return 0;
}

