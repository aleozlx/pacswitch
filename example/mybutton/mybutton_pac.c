#include "mybutton_pac.h"
#include "pacswitchcli.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char user[80],receiver[80],*password;
static void (*_lightRequest)(int);
static void OnDataReceived(char *buffer,ssize_t length){
	//fprintf(stderr, "@%d\n", (int)_lightRequest);
	if (_lightRequest!=NULL){
		if (buffer[length-1]=='N')_lightRequest(1);
		else _lightRequest(0);
	}
	
}

void mybuttonpacInit(){
	strcpy(user,"test");
	strcpy(receiver,"test");
	password=(char*)malloc(80);
	strcpy(password,"1234");
	if(pacInit(user,password,receiver,"222.69.93.107","mybutton")<0){
		printf("Error.\n");
	}
	free(password);	
	pacOnDataReceived(OnDataReceived);
}

void mybuttonpacSendLightEvent(int v){
	if(v) pacSendData("ON",2,NULL);
	else pacSendData("OFF",3,NULL);;
}

void mybuttonpacLightRequest(void (*func)(int)) {_lightRequest=func; }
