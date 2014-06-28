// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.lang.*;
import java.util.*;
import java.io.*;
import java.net.*;

class FutureObject<T>{
	public T value=null;
	public boolean isAvailable=false;
}

/**
 * PacswitchMessager
 * @author Alex
 * @since June 27, 2014
 */
public abstract class PacswitchMessager extends PacswitchClient {
	/**
	 * Message encoding
	 */
	public static final String ENC="utf-8";

	/**
	 * Request ID length
	 */
	private static final int RIDLEN=20;

	/**
	 * Request flag
	 */
	protected static final byte[] REQFLAG={RIDLEN};

	/**
	 * Response flag
	 */
	protected static final byte[] RESFLAG={0};

	/**
	 * Authentication state
	 */
	int _isAuthenticated=666;

	/**
	 * Request/response mapping
	 */
	protected Map<String,FutureObject<String>> msgmap=new HashMap<String,FutureObject<String>>();

	/**
	 * Incoming connection mapping
	 */
	protected Map<String,FutureObject<Socket>> sockmap=new HashMap<String,FutureObject<Socket>>();

	/**
	 * Request ID range
	 */
	protected static final char[] ridRange="0123456789abcdefghjkmnpqrstuvwxyz".toCharArray();

	/**
	 * Request ID length
	 * @param userid User ID
	 * @param password User password
	 * @param host Host IP address
	 * @param clienttype Client type
	 * @return Whether initialized successfully.
	 */
	public boolean connect(String userid,String password,String host,String clienttype){
		if(!this.pacInit(userid,password,host,clienttype))return false;
		else{ this.start(); this._isAuthenticated=0; return true; }
	}

	/**
	 * Authentication state.
	 * @return msg Authentication state
	 */
	public boolean isAuthenticated(){ 
		if(this._isAuthenticated==666)return false;
		while(this._isAuthenticated==0)this.wait(50);
		return this._isAuthenticated==1; 
	}

	/**
	 * Handle a response or a request.
	 * @param sender Sender ID
	 * @param buffer User data
	 */
	@Override
	public final void onDataReceived(String sender,byte[] buffer){
		String message;
		try{ message=new String(buffer,RIDLEN+1,buffer.length-RIDLEN-1,ENC); }
		catch(UnsupportedEncodingException e){ return; }
		if(buffer[0]==REQFLAG[0]){ // Request received
			String response=this.handleMessage(sender,message);
			try{ this.sendDataFields(sender,RESFLAG,Arrays.copyOfRange(buffer,1,RIDLEN+1),response.getBytes(ENC)); }
			catch(UnsupportedEncodingException e){ }
		}
		else if(buffer[0]==0){ // Response received
			try{
				String requestID=new String(buffer,1,RIDLEN,ASCII);
				FutureObject<String> mr=msgmap.get(requestID);
				if(mr!=null){
					mr.value=message;
					mr.isAvailable=true;
				}
			}
			catch(UnsupportedEncodingException e){ }
		}
	}

	/**
	 * Handle a server response.
	 * @param msg Server response message
	 */
	@Override
	public final void onServerResponse(String msg){
		String[] title_body=msg.split(": ");
		if(title_body.length==2){
			String title=title_body[0],body=title_body[1];
			if(title.equals("LOGIN")){
				if(body.equals("OK"))this._isAuthenticated=1;
				else this._isAuthenticated=-1;
			}
			else if(title.equals("INVITE")){
				/*
				create socket and initialize it
				initiate new thread and call acceptSocket
				put message to response the invite code to other side
				*/
			}
		}
	}

	/**
	 * Send a message consists of multiple fields.
	 * @param to Receiver ID
	 * @param fields Message fields
	 * @return Whatever pacSendData returns
	 */
	protected final boolean sendDataFields(String to, byte[] ... fields){
		ByteArrayOutputStream buffer=new ByteArrayOutputStream();
		for(byte[] i:fields)buffer.write(i,0,i.length);
		return pacSendData(buffer.toByteArray(),to);
	}

	/**
	 * Send a message.
	 * @param to Receiver ID
	 * @param message Message content
	 * @return Response from other side
	 * @throw PacswitchException
	 */
	public String sendMessage(String to, String message) throws PacswitchException{
		if(this.isAuthenticated()){
			Random r=new Random();
			char[] ridbuffer=new char[RIDLEN];
			for(int i=0;i<RIDLEN;i++)ridbuffer[i]=ridRange[r.nextInt(ridRange.length)];
			String requestID=new String(ridbuffer);
			FutureObject<String> mr=new FutureObject<String>();
			this.msgmap.put(requestID,mr);
			try{
				if(this.sendDataFields(to,REQFLAG,requestID.getBytes(ASCII),message.getBytes(ENC))){
					for(int tries=0;tries<65&&!mr.isAvailable;tries++)this.wait(30);
					if(mr.isAvailable)return mr.value;
					else throw new UnreachableException(to,"No response");
				}
				else throw new UnreachableException(to,"Offline");
			}
			catch(UnsupportedEncodingException e){ throw new PacswitchException("Unsupported encoding",e); }
			finally{ this.msgmap.remove(requestID); }
		}
		else throw new PacswitchException("Not authenticated");
	}

	public Socket createSocket(String to, String device){
		/*
		send special message for a new socket
		wait for invite code
		create socket and initialize it
		return socket
		*/
		return null;
	}

	public void acceptSocket(String from, Socket s){
		/*
		[abstract method] called in a new thread
		*/
	}

	/**
	 * Handle a message.
	 * @param from Sender ID
	 * @param message Message content
	 * @return Response to the message
	 */
	public abstract String handleMessage(String from, String message);
}
