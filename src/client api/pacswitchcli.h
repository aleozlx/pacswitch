#ifndef __PACSWITCHCLI_H_
#define __PACSWITCHCLI_H_
#define SZ_PACKAGE_START 10
#define SZ_PACKAGE_END 10
#define SZ_PACKAGE_TEXT 10
#define SZ_BUFFER 32768
#include <sys/types.h>

int pacInit(
	const char *user,
	const char *password,
	const char *receiver,
	const char *host,
	const char *clienttype
);

void pacClose();
int pacSocketno();
void pacStart(const char *recv);
void pacEnd();
void pacSendData(const char *buffer,ssize_t length,const char *recv);
void pacOnDataReceived(void (*func)(char*,ssize_t));
int pacLoop();
#endif

