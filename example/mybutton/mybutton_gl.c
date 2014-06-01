#include <GL/glut.h>
#include "mybutton_gl.h"
#define MOUSE_XY(_x,_y) _x=xMouse;_y=window.height-yMouse
struct{ int x1,x2,y1,y2,clicks; } mouse; 
struct{ int width,height; } window;

int light=0;

void keepAliveHandler(int id){ glutPostRedisplay(); glutTimerFunc(50,keepAliveHandler,1); }

void setLight(int v){ light=(v!=0); }
void (*_lightChanged)(int);
void onLightChanged(void (*func)(int)){ _lightChanged=func; }

void display(){
	if (light) glClearColor(1.0,1.0,1.0,0.0);
	else glClearColor(0.0,0.0,0.0,0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	glBegin(GL_POINTS);
	if(light)glColor3f(1.0,1.0,1.0);
	else glColor3f(0.0,0.0,0.0);
	glVertex3f(0,30,0);
	glEnd();
	//circle(200,150,100);
	//if (mouse.clicks>=1)circle(mouse.x1,mouse.y1,sqrt((mouse.x1-mouse.x2)*(mouse.x1-mouse.x2)+(mouse.y1-mouse.y2)*(mouse.y1-mouse.y2)));
	
	glutSwapBuffers();
}

void onclick(GLint button,GLint action,GLint xMouse,GLint yMouse){
	if(button==GLUT_LEFT_BUTTON&&action==GLUT_DOWN){
		// if(mouse.clicks==0||mouse.clicks==2){ 
		// 	mouse.clicks=1; 
		// 	MOUSE_XY(mouse.x1,mouse.y1);
		// }
		// else{ 
		// 	mouse.clicks=2; 
		// 	MOUSE_XY(mouse.x2,mouse.y2); 
		// 	glutPostRedisplay(); 
		// }
		light=!light;
		glutPostRedisplay(); 
		if (_lightChanged!=NULL){
			_lightChanged(light);
		}
	}
	// if(button==GLUT_RIGHT_BUTTON&&action==GLUT_DOWN){ 
	// 	mouse.clicks=0; 
	// 	glutPostRedisplay(); 
	// }
}

void onmove(GLint xMouse,GLint yMouse){
	// if(mouse.clicks==1){ 
	// 	MOUSE_XY(mouse.x2,mouse.y2); 
	// 	glutPostRedisplay(); 
	// }
	glutPostRedisplay(); 
}

void onresize(int w,int h){
	window.width=w;window.height=h;
	glViewport(0,0,w,h);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluOrtho2D(0.0,window.width,0.0,window.height);
}

int gInit(int* argcp, char* argv[]){
	glutInit(argcp,argv);
	glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB);
	glutInitWindowSize(400,300);
	glutInitWindowPosition(300,300);
	glutCreateWindow("Mybutton");
	glutDisplayFunc(display);
	glutMouseFunc(onclick);
	glutReshapeFunc(onresize);
	glutPassiveMotionFunc(onmove);
	glClearColor(1.0,1.0,1.0,0.0);
	glColor3f(0.0,0.0,1.0);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluOrtho2D(0.0,500.0,0.0,500.0);
	glMatrixMode(GL_MODELVIEW);

	_lightChanged=NULL;

	
	return 0;
}

void gLoop(){

	glutTimerFunc(50,keepAliveHandler,1);
	glutMainLoop();
}
