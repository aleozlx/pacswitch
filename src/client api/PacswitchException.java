// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.io.*;
import java.net.*;
import java.lang.*;

public class PacswitchException extends Exception {
	public PacswitchException(){
		super();
	}

	public PacswitchException(String message){
		super(message);
	}

	public PacswitchException(String message, Throwable cause){
		super(message,cause);
	}
}
