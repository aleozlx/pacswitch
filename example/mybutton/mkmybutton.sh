#!/bin/bash
if [ -f "mybutton" ]; then 
	rm mybutton 
fi
gcc -O2 -Wall -Wno-unused-result -o mybutton mybutton_pac.c mybutton_gl.c mybutton.c libpacswitchcli.a -lGL -lGLU -lglut
#gcc -O2 -Wall -Wno-unused-result -o mybutton pacswitchcli.c mybutton_pac.c mybutton_gl.c mybutton.c -lGL -lGLU -lglut
