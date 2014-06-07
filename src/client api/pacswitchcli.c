// Fork me on GitHub! https://github.com/aleozlx/pacswitch
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <arpa/inet.h>
#include "pacswitchcli.h"

//gcc -O2 -Wno-unused-result -c pacswitchcli.c
//ar crv libmyhello.a hello.o

const char* PACKAGE_START = "\x05" "ALXPACSVR";
const char* PACKAGE_END = "\x17" "CESTFINI" "\x04";
const char* PACKAGE_TEXT = "\x02(TXTPAC)\n";

struct mybuffer{
	char buffer[SZ_BUFFER];
	ssize_t size;
} strin, strout, strtmp;

static struct sockaddr_in server_addr; int s=0;
static char _receiver[255]; size_t sz_receiver=0;
static void (*_onDataReceived)(char*,ssize_t);

int pacInit(
	const char *user,
	const char *password,
	const char *receiver,
	const char *host,
	const char *clienttype
){
	s=socket(AF_INET,SOCK_STREAM,0);
	if(s<0) return -1; //socket error
	bzero(&server_addr,sizeof(server_addr));
	server_addr.sin_family=AF_INET;
	server_addr.sin_addr.s_addr=htonl(INADDR_ANY);
	server_addr.sin_port=htons(3512);
	inet_pton(AF_INET,host,&server_addr.sin_addr);
	if(connect(s,(struct sockaddr*)&server_addr,sizeof(struct sockaddr))<0)return -2; //network error

	if(receiver!=NULL){
		strcpy(_receiver,receiver);
		strcat(_receiver,"\n");
		sz_receiver=strlen(_receiver);
	}

	_onDataReceived=NULL;

	write(s,PACKAGE_START,SZ_PACKAGE_START);
	write(s,PACKAGE_TEXT,SZ_PACKAGE_TEXT);
	// AUTH username password client_type
	write(s,"AUTH ",5); 
	write(s,user,strlen(user)); 
	write(s," ",1); 
	write(s,password,strlen(password)); 
	write(s," ",1);
	write(s,clienttype,strlen(clienttype));
	write(s,PACKAGE_END,SZ_PACKAGE_END);
	return 0;
}

inline void pacClose(){
	close(s);
}

inline int pacSocketno(){
	return s;
}

void pacStart(const char *recv){
	write(s,PACKAGE_START,SZ_PACKAGE_START);
	if (recv!=NULL) {
		write(s,recv,strlen(recv));
		write(s,"\n",1);
	}
	else write(s,_receiver,strlen(_receiver));
}

void pacEnd(){
	write(s,PACKAGE_END,SZ_PACKAGE_END);
}

void pacSendData(const char *buffer,ssize_t length,const char *recv){
	pacStart(recv);
	write(s,buffer,length);
	pacEnd();
}

void pacOnDataReceived(void (*func)(char*,ssize_t)){
	_onDataReceived=func;
}

int pacLoop(){
	strin.size=0; strin.buffer[0]='\0';
	while(1){ 
		char *iI,*iII;
		while(strin.size!=0&&(iI=strstr(strin.buffer,PACKAGE_START))!=NULL&&(iII=strstr(strin.buffer,PACKAGE_END))!=NULL){
			strncpy(strtmp.buffer,iI+SZ_PACKAGE_START,strtmp.size=iII-(iI+SZ_PACKAGE_START));
			//strtmp.buffer[strtmp.size]='\n';
			//write(1,strtmp.buffer,strtmp.size+1);

			//fprintf(stderr, "@@%d\n", (int)_onDataReceived);
			if(_onDataReceived!=NULL)_onDataReceived(strtmp.buffer,strtmp.size);

			strncpy(strtmp.buffer,iII+SZ_PACKAGE_END,strtmp.size=strin.buffer+strin.size-(iII+SZ_PACKAGE_END));
			strncpy(strin.buffer,strtmp.buffer,strin.size=strtmp.size);
			strin.buffer[strin.size]='\0';
		}
		strtmp.size=read(s,strtmp.buffer,2048);
		if(strtmp.size<=0) sleep(600);
		else if(strtmp.size>0&&strtmp.size+strin.size<SZ_BUFFER-1){
			strncpy(strin.buffer+strin.size,strtmp.buffer,strtmp.size);
			strin.size+=strtmp.size;
			strin.buffer[strin.size]='\0';
		}
		else return -1; //buffer overflow
	}
	return 0;
}

