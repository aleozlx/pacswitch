// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;

public class PacswitchException extends Exception {
	private static final long serialVersionUID = 6097161643360603291L;
	public PacswitchException(){ super(); }
	public PacswitchException(String message){ super(message); }
	public PacswitchException(String message, Throwable cause){ super(message,cause); }
}
