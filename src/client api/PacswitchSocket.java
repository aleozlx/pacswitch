// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.net.*;
import java.io.*;

public class PacswitchSocket extends Socket{
	protected String to,device,id;
	FutureObject<Integer> _isAuthenticated=new FutureObject<Integer>(Synchronizer.AUTH_DEFAULT);
	protected PacswitchSocket(PacswitchMessager m) throws IOException{ super(m.host,m.port); }
	public final String getReceiver(){ return this.to; }
	public final String getDevice(){ return this.device; }
	public final String getId(){ return this.id; }
	public final boolean isAuthenticated(){ return Synchronizer.isAuthenticated(this._isAuthenticated); }
}
