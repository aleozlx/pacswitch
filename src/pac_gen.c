#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

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
} strout;

#define SZ_TEST_PAC 2048

const char *receiver="alex\n";

int main(void){
	int s;
	memset(strout.buffer,0xCC,SZ_TEST_PAC);
	s=open("pacgen.bin",O_WRONLY|O_CREAT,S_IRUSR|S_IRGRP|S_IROTH);
	for (unsigned int i = 0; i < 122880; ++i){
		write(s,PACKAGE_START,SZ_PACKAGE_START);
		write(s,receiver,strlen(receiver));
		write(s, strout.buffer, SZ_TEST_PAC);
		write(s,PACKAGE_END,SZ_PACKAGE_END);
	}
	close(s);
	return 0;
}