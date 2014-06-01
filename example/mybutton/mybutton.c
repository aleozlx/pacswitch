#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/types.h>
#include "mybutton_gl.h"
#include "mybutton_pac.h"

static int prun=1;
static int pretval;
void onExit(){ pacClose(); }

void *start_routine(void *arg){
	mybuttonpacInit();
	mybuttonpacLightRequest(setLight);
	pacLoop();
	pretval=0;
	pthread_exit(&pretval);
}

int main(int argc, char* argv[]){
	pthread_t pt;
	int ret=-1;
	atexit(onExit);
	ret=pthread_create(&pt,NULL,(void*)start_routine,&prun);

	if(ret!=0){
		printf("Error: cannot create thread\n");
		exit(0);
	}

	gInit(&argc,argv);
	onLightChanged(mybuttonpacSendLightEvent);
	gLoop();
	return 0;
}
