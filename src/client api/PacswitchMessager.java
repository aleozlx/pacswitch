// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.util.*;
import java.io.*;

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

	protected static final String SVRRES_STREAM="SVRRES_STREAM";

	protected static final String STREAM_DENIED="";

	/**
	 * Request ID length
	 */
	private static final int RIDLEN=20;

	/**
	 * Authentication state
	 */
	FutureObject<Integer> _isAuthenticated=new FutureObject<Integer>(Synchronizer.AUTH_DEFAULT);

	/**
	 * Request/response mapping
	 */
	protected Map<String,FutureObject<String>> msgmap=new HashMap<String,FutureObject<String>>();

	/**
	 * Incoming connection mapping
	 */
	protected Map<String,FutureObject<PacswitchSocket>> sockmap=new HashMap<String,FutureObject<PacswitchSocket>>();

	/**
	 * Request ID range
	 */
	protected static final char[] ridRange="0123456789abcdefghjkmnpqrstuvwxyz".toCharArray();

	protected String device;

	/**
	 * Request ID length
	 * @param userid User ID
	 * @param password User password
	 * @param host Host IP address
	 * @param clienttype Client type
	 * @return Whether initialized successfully.
	 */
	public boolean connect(String userid,String password,String device,String host,String clienttype){
		this.device=device;
		this._isAuthenticated.reset();
		if(!this.pacInit(userid,password,host,clienttype))return false;
		else{ this.start(); this._isAuthenticated.value=Synchronizer.NOT_AVAILABLE; return true; }
	}

	/**
	 * Authentication state.
	 * @return msg Authentication state
	 */
	public final boolean isAuthenticated(){ return Synchronizer.isAuthenticated(this._isAuthenticated); }

	public final String getDeviceName(){ return this.device; }

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
		switch(MessageType.fromByte(buffer[0])){
		case REQUEST:
			String response=this.handleMessage(sender,message);
			try{ 
				this.sendDataFields(sender,
					MessageType.RESPONSE.getData(),
					Arrays.copyOfRange(buffer,1,RIDLEN+1),
					response.getBytes(ENC)); 
			}
			catch(UnsupportedEncodingException e){ }
			break;
		case RESPONSE:
			try{
				String requestID=new String(buffer,1,RIDLEN,ASCII);
				FutureObject<String> mr=msgmap.get(requestID);
				if(mr!=null)mr.set(message);
			}
			catch(UnsupportedEncodingException e){ }
			break;
		case STREAMREQ:
			if(message.equals(this.getDeviceName())){
				try{ 
					if(!msgmap.containsKey(SVRRES_STREAM))msgmap.put(SVRRES_STREAM,new FutureObject<String>());
					FutureObject<String> svrres=msgmap.get(SVRRES_STREAM);
					STREAM(); 
					svrres.until(10,60);
					if(svrres.isAvailable()){
						String[] invitecode=svrres.get().split(" ");
						
									/*
			create socket and initialize it
			initiate new thread and call acceptSocket
			response the invite code to other side
			*/
					}
				}
				catch(IOException e){ }
			}
			else{
				try{ 
					this.sendDataFields(sender,
						MessageType.STREAMRES.getData(),
						Arrays.copyOfRange(buffer,1,RIDLEN+1),
						STREAM_DENIED.getBytes(ENC)); 
				}
				catch(UnsupportedEncodingException e){ }
			}
			break;
		case STREAMRES:
			
			//create socket and initialize it
			break;

		}
	}

	/**
	 * Handle a server response.
	 * @param msg Server response message
	 */
	@Override
	public final void onServerResponse(String title, String msg){
		if(title.equals("LOGIN")){
			if(msg.equals("OK"))this._isAuthenticated.set(Synchronizer.OK);
			else this._isAuthenticated.set(Synchronizer.FAILED);
		}
		else if(title.equals("STREAM")){
			FutureObject<String> svrres=msgmap.get(SVRRES_STREAM);
			if(svrres!=null)svrres.set(msg);
		}
	}

	/**
	 * Send a message.
	 * @param to Receiver ID
	 * @param message Message content
	 * @return Response from other side
	 * @throw PacswitchException
	 */
	public final String send(String to, String message) throws PacswitchException{
		FutureObject<String> mr=null;
		PacswitchException e;
		try{ 
			mr=this._send(MessageType.REQUEST,to,message); 
			e=mr.getException();
			if(e!=null)throw e;
			return mr.get(Synchronizer.TIMEOUT_DEFALUT,new UnreachableException(to,"No response"));
		}
		finally{ if(mr!=null)this.msgmap.remove(mr.getTag()); }
	}

	protected final FutureObject<String> _send(MessageType msgtype,String to, String message){
		FutureObject<String> mr=new FutureObject<String>();
		if(this.isAuthenticated()){
			Random r=new Random();
			char[] ridbuffer=new char[RIDLEN];
			for(int i=0;i<RIDLEN;i++)ridbuffer[i]=ridRange[r.nextInt(ridRange.length)];
			String requestID=new String(ridbuffer);
			mr.tag=requestID;
			this.msgmap.put(requestID,mr);
			try{
				if(this.sendDataFields(to,
					msgtype.getData(),
					requestID.getBytes(ASCII),
					message.getBytes(ENC))) return mr;
				else return mr.exceptionSugar(new UnreachableException(to,"Offline"));
			}
			catch(UnsupportedEncodingException e){ return mr.exceptionSugar(new PacswitchException("Unsupported encoding",e)); }
		}
		else return mr.exceptionSugar(new PacswitchException("Not authenticated"));
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

	protected final FutureObject<PacswitchSocket> _punch(String to, String device){
		FutureObject<PacswitchSocket> r=new FutureObject<PacswitchSocket>();
		FutureObject<String> sres=this._send(MessageType.STREAMREQ,to,device);
		PacswitchException e=sres.getException();
		r.tag=sres.getTag();
		if(e!=null)return r.exceptionSugar(e);
		else{ sockmap.put(sres.getTag(),r); return r; }
	}

	public void acceptSocket(String from, PacswitchSocket s){ }

	/**
	 * Handle a message.
	 * @param from Sender ID
	 * @param message Message content
	 * @return Response to the message
	 */
	public abstract String handleMessage(String from, String message);
}
