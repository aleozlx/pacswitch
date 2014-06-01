#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
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
} strin, strtmp;

unsigned int pac_count=0;

void onDataReceived(char* buffer,ssize_t length){
	pac_count++;
}

int main(void){
	strin.size=0; strin.buffer[0]='\0';
	while(1){ 
		char *iI,*iII;
		while(strin.size!=0&&(iI=strstr(strin.buffer,PACKAGE_START))!=NULL&&(iII=strstr(strin.buffer,PACKAGE_END))!=NULL){
			strncpy(strtmp.buffer,iI+SZ_PACKAGE_START,strtmp.size=iII-(iI+SZ_PACKAGE_START));
			//strtmp.buffer[strtmp.size]='\n';
			//write(1,strtmp.buffer,strtmp.size+1);

			//fprintf(stderr, "@@%d\n", (int)_onDataReceived);
			onDataReceived(strtmp.buffer,strtmp.size);

			strncpy(strtmp.buffer,iII+SZ_PACKAGE_END,strtmp.size=strin.buffer+strin.size-(iII+SZ_PACKAGE_END));
			strncpy(strin.buffer,strtmp.buffer,strin.size=strtmp.size);
			strin.buffer[strin.size]='\0';
		}
		strtmp.size=read(0,strtmp.buffer,2048);
		if(strtmp.size<=0) break;
		else if(strtmp.size>0&&strtmp.size+strin.size<SZ_BUFFER-1){
			strncpy(strin.buffer+strin.size,strtmp.buffer,strtmp.size);
			strin.size+=strtmp.size;
			strin.buffer[strin.size]='\0';
		}
		else return -1; //buffer overflow
	}
	printf("%d\n", pac_count);
	return 0;
}


// time ./pac_counter < pacgen.bin                                                                  18:02
// 122880
// ./pac_counter < pacgen.bin  0.55s user 0.18s system 99% cpu 0.735 total



