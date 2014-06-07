// Fork me on GitHub! https://github.com/aleozlx/pacswitch
package com.aleozlx.pacswitch;
import java.io.*;
import java.net.*;
import java.lang.*;

class Mybuffer{
	public static final int SZ_BUFFER=32768;
	public byte[] buffer=new byte[SZ_BUFFER];
	public int size=0;
	protected int find(byte[] s2,int start){
		for(int i=start;i<this.size;i++)
			for(int j=0;j<s2.length&&i+j<this.size&&this.buffer[i+j]==s2[j];j++)
				if(j==s2.length-1)return i;
		return -1;
	}	
	protected int find(byte[] s2){ return find(s2,0); }	
}

/**
 * Pacswitch client
 * @author Alex
 * @version 1.1.0
 * @since June 3, 2014
 */
public abstract class PacswitchClient {
	public static final byte[] PACKAGE_START={5,65,76,88,80,65,67,83,86,82};
	public static final byte[] PACKAGE_END={23,67,69,83,84,70,73,78,73,4};
	public static final byte[] PACKAGE_TEXT={2,40,84,88,84,80,65,67,41,10};
	public static final byte[] SPACE={32};
	public static final byte[] NEWLINE={10};
	public static final byte[] SENDER_SEP={62,32};
	protected static final String ASCII="ascii";
	protected Mybuffer mybuffer=new Mybuffer();
	protected String user;
	protected String password;
	protected String host;
	protected String clienttype;
	public boolean autoReconnect=true;
	public Socket socket;

	/**
	 * Initiate a connection.
	 * @param user User account
	 * @param password Password
	 * @param host Host IP Address
	 * @param clienttype A unique string that distinguishes different kind of clients
	 * @return Whether a connection is sucessfully made.
	 */
	public boolean pacInit(String user,String password,String host,String clienttype){
		try{
			socket=new Socket(host,3512);
			this.user=user;
			this.password=password;
			this.host=host;
			this.clienttype=clienttype;
			AUTH();
		}
		catch(IOException e){ return false; }
		return true;
	}

	protected void AUTH() throws IOException{
		OutputStream os=socket.getOutputStream();
		os.write(PACKAGE_START);
		os.write(PACKAGE_TEXT);
		// AUTH username password client_type
		os.write("AUTH ".getBytes(ASCII)); 
		os.write(user.getBytes(ASCII)); 
		os.write(SPACE); 
		os.write(password.getBytes(ASCII)); 
		os.write(SPACE); 
		os.write(clienttype.getBytes(ASCII));
		os.write(PACKAGE_END);
	}

	protected boolean reconnect(){
		while(autoReconnect){
			this.closeSocket();
			try{ 
				socket=new Socket(host,3512);
				AUTH();
				return true;
			}
			catch(IOException e){
				try{ Thread.sleep(800); }
				catch(InterruptedException e2){ Thread.currentThread().interrupt(); }
			}
		}
		return false;
	} 

	/**
	 * Send user data, which will be automatically wrapped in a packet.
	 * @param buffer User data
	 * @param recv Receiver account
	 */
	public boolean pacSendData(byte[] buffer,String recv) {
		while(true){
			try{ 
				OutputStream os=socket.getOutputStream(); 
				os.write(PACKAGE_START);
				os.write(recv.getBytes(ASCII));
				os.write(NEWLINE);
				os.write(buffer);
				os.write(PACKAGE_END);
				break;
			}
			catch(IOException e){
				try{ Thread.sleep(2000); }
				catch(InterruptedException e2){ Thread.currentThread().interrupt(); }
			}
		}
		return true;
	}

	/**
	 * Start an event loop for response data.
	 * @throws InterruptedException
	 */
	public void pacLoop() throws InterruptedException{
		byte[] _mybuffer=new byte[2048]; int sz_mybuffer,iI,iII,iIII;
		do{
			while(mybuffer.size!=0&&(iI=mybuffer.find(PACKAGE_START))!=-1&&(iII=mybuffer.find(PACKAGE_END))!=-1){
				iIII=mybuffer.find(SENDER_SEP,iI+PACKAGE_START.length);
				String sender=new String(mybuffer.buffer,iI+PACKAGE_START.length,iIII-(iI+PACKAGE_START.length));
				byte[] data=new byte[iII-(iIII+SENDER_SEP.length)];
				System.arraycopy(mybuffer.buffer,iIII+SENDER_SEP.length,data,0,data.length);
				if(sender.equals("pacswitch")){
					try{onServerResponse(new String(data,ASCII));}
					catch(UnsupportedEncodingException ee){ }
				}
				else onDataReceived(sender,data); 
				iII+=PACKAGE_END.length;
				System.arraycopy(mybuffer.buffer,iII,mybuffer.buffer,0,mybuffer.size-=iII);
			}
			try{
				InputStream is=socket.getInputStream();
				sz_mybuffer=is.read(_mybuffer);
				if(sz_mybuffer<=0)throw new IOException("Connection lost");
				else if(sz_mybuffer>0&&sz_mybuffer+mybuffer.size<Mybuffer.SZ_BUFFER-1){
					System.arraycopy(_mybuffer,0,mybuffer.buffer,mybuffer.size,sz_mybuffer);
					mybuffer.size+=sz_mybuffer;
				}
				else sz_mybuffer=0;
			}
			catch(IOException e){ 
				Thread.sleep(600); 
				if(!reconnect()) break;
			}
		} while(true);
	}

	/**
	 * Start an event loop asynchronously for response data.
	 */
	public void start(){
		new Thread(){
			@Override
			public void run(){
				try{ pacLoop(); }
				catch(InterruptedException e){ this.interrupt(); }
			}
		}.start();
	}

	/**
	 * Implement this to handle data received.
	 * @param sender Sender account
	 * @param buffer User data
	 */
	public abstract void onDataReceived(String sender,byte[] buffer);

	// /**
	//  * Override this to handle severe network error.
	//  * This is only called when there is no way to continue.
	//  * @param e IOException
	//  */
	// public void onNetworkError(IOException e){ }

	/**
	 * Override this to handle server response messages
	 * @param msg Server response message
	 */
	public void onServerResponse(String msg){ }

	/**
	 * Close a connection permanently.
	 */
	public void close(){ 
		this.autoReconnect=false;
		this.closeSocket(); 
	}

	protected void closeSocket(){
		try{ if(socket!=null)socket.close(); }
		catch(Exception e){ }
	}
}
