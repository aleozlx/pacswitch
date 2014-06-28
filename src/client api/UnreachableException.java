// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.io.*;
import java.net.*;
import java.lang.*;

public class UnreachableException extends PacswitchException {
	public String target;
	public UnreachableException(String to,String errmsg){
		super(errmsg);
		this.target=to;
	}
}
