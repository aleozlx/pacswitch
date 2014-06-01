#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <time.h>

#define SZ_PACKAGE_START 10
const char* PACKAGE_START = "\x05" "ALXPACSVR";

#define SZ_PACKAGE_END 10
const char* PACKAGE_END = "\x17" "CESTFINI" "\x04";

#define SZ_PACKAGE_TEXT 10
const char* PACKAGE_TEXT = "\x02(TXTPAC)\n";

#define SZ_BUFFER 32768
struct mybuffer{
	char buffer[SZ_BUFFER];
	ssize_t size;
} strin, strout, strtmp;

char user[80],receiver[80],*password;

enum conn_status {OFFLINE=1,ESTABLISHED=0} status;

int main(int argc, char const *argv[]){
	int s=0,t; int recv_mode=0; time_t tim0,tim1;
	struct sockaddr_in server_addr;
	status=OFFLINE;

	if(argc==2){
		strcpy(receiver,argv[1]);
		strcat(receiver,"\n");
	}
	else{
		printf("Usage: %s receiver|--recv\n",argv[0]);
		return status;
	}

	if(strcmp(receiver,"--recv\n")==0)recv_mode=1;

	s=socket(AF_INET,SOCK_STREAM,0);
	if(s<0){
		printf("Error: socket error\n");
		return status;
	}

	bzero(&server_addr,sizeof(server_addr));
	server_addr.sin_family=AF_INET;
	server_addr.sin_addr.s_addr=htonl(INADDR_ANY);
	server_addr.sin_port=htons(3512);
	inet_pton(AF_INET,"222.69.93.107",&server_addr.sin_addr);
	if((t=connect(s,(struct sockaddr*)&server_addr,sizeof(struct sockaddr)))<0){
		printf("Error: network error\n");
		return status;
	}
	else status=ESTABLISHED;

	printf("Pacswitch speed test. May 2014 (C) Alex\n");
	printf("Name: "); scanf("%s",user);
	password = getpass("Password: ");

	write(s,PACKAGE_START,SZ_PACKAGE_START);
	write(s,PACKAGE_TEXT,SZ_PACKAGE_TEXT);
	// AUTH username password client_type
	write(s,"AUTH ",5); write(s,user,strlen(user)); write(s," ",1); write(s,password,strlen(password)); write(s," pacspeed\n",10);
	// MASS
	write(s,"MASS",4);
	write(s,PACKAGE_END,SZ_PACKAGE_END);
	free(password);
	
	if(recv_mode){ // socket -> tty
		strin.size=0; strin.buffer[0]='\0';
		printf("Receiver mode\n");
		while(1){ 
			char *iI,*iII; 
			double dt; time(&tim0); tim1=tim0;
			while(strin.size!=0&&(iI=strstr(strin.buffer,PACKAGE_START))!=NULL&&(iII=strstr(strin.buffer,PACKAGE_END))!=NULL){
				dt=difftime(tim1,tim0); time(&tim1);
				fprintf(stderr, "[%dKB]", (iII-(iI+SZ_PACKAGE_START))>>10);
				strncpy(strtmp.buffer,iI+SZ_PACKAGE_START,strtmp.size=iII-(iI+SZ_PACKAGE_START));
				strncpy(strtmp.buffer,iII+SZ_PACKAGE_END,strtmp.size=strin.buffer+strin.size-(iII+SZ_PACKAGE_END));
				strncpy(strin.buffer,strtmp.buffer,strin.size=strtmp.size);
				strin.buffer[strin.size]='\0';
			}
			strtmp.size=read(s,strtmp.buffer,2048);
			if(strtmp.size<=0){ sleep(600); write(1," ",1); }
			else if(strtmp.size>0&&strtmp.size+strin.size<SZ_BUFFER-1){
				strncpy(strin.buffer+strin.size,strtmp.buffer,strtmp.size);
				strin.size+=strtmp.size;
				strin.buffer[strin.size]='\0';
				write(1,"+",1);
			}
			else{
				printf("buffer overflow\n");
				exit(0);
			}
		}
	}
	else{ // tty -> socket
		#define SZ_TEST_PAC 2048
		#define TEST_TIME 15.0
		double dt; time(&tim0); tim1=tim0; strout.size=SZ_TEST_PAC; int pacct=0;
		memset(strout.buffer,0xCC,SZ_TEST_PAC);
		do{
			dt=difftime(tim1,tim0); time(&tim1);
			write(s,PACKAGE_START,SZ_PACKAGE_START);
			write(s,receiver,strlen(receiver));
			write(s,strout.buffer,strout.size);
			write(s,PACKAGE_END,SZ_PACKAGE_END);
			pacct++;
		} while (dt<TEST_TIME);
		printf("%.1lfKB/s\n", ((double)((SZ_TEST_PAC*pacct)>>10))/TEST_TIME);
	}

	close(s);
	return status;
}

