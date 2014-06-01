//gcc -O2 -Wall -Wno-unused-result -o pacspeed pacspeed.c libpacswitchcli.a
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include "pacswitchcli.h"

char user[80],receiver[80],*password,outputbuffer[SZ_BUFFER];

void OnDataReceived(char* buffer,ssize_t length){
	fprintf(stderr, "[%dKB]", length>>10);
}

int main(int argc, char const *argv[]){
	int conn; int recv_mode=0; time_t tim0,tim1;

	if(argc==2)strcpy(receiver,argv[1]);
	else{
		printf("Usage: %s receiver\n",argv[0]);
		return 1;
	}
	if(strcmp(receiver,"--recv")==0)recv_mode=1;
	printf("Pacswitch speed test. May 2014 (C) Alex\n");
	printf("Name: "); scanf("%s",user);
	password = getpass("Password: ");

	conn=pacInit(user,password,receiver,"222.69.93.107","pacspeed");
	free(password);
	switch(conn){
		case -1: printf("Error: socket error\n"); return 1;
		case -2: printf("Error: network error\n"); return 1;
	}
	pacOnDataReceived(OnDataReceived);
	if(recv_mode){
		printf("Receiver mode\n");
		time(&tim0); tim1=tim0;
		pacLoop();
	}
	else{
		#define SZ_TEST_PAC 2048
		#define TEST_TIME 15.0
		double dt; time(&tim0); tim1=tim0; int pacct=0;
		memset(outputbuffer,0xCC,SZ_TEST_PAC);
		do{
			dt=difftime(tim1,tim0); time(&tim1);
			pacSendData(outputbuffer,SZ_TEST_PAC,receiver);
			pacct++;
		} while (dt<TEST_TIME);
		printf("%.1lfKB/s\n", ((double)((SZ_TEST_PAC*pacct)>>10))/TEST_TIME);
	}
	pacClose();
	return 0;
}

