// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;

public class UnreachableException extends PacswitchException {
	private static final long serialVersionUID = 587189063521112980L;
	public String target;
	public UnreachableException(String to,String errmsg){
		super(errmsg);
		this.target=to;
	}
}
