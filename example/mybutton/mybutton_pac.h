#ifndef __MYBUTTON_PAC_H_
#define __MYBUTTON_PAC_H_
#include "pacswitchcli.h"
void mybuttonpacSendLightEvent(int v);
void mybuttonpacLightRequest(void (*func)(int));
void mybuttonpacInit();
#endif
