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
 * @version 1.0.0
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
		catch(IOException e){
			e.printStackTrace();
			return false;
		}
		return true;
	}

	/**
	 * Close a connection.
	 */
	public void pacClose(){
		try{ socket.close(); }
		catch(IOException e){ e.printStackTrace(); }
	}

	/**
	 * Send header of a packet.
	 * @param recv Receiver account
	 * @throws IOException
	 */
	public void pacStart(String recv) throws IOException {
		OutputStream os=socket.getOutputStream();
		os.write(PACKAGE_START);
		os.write(recv.getBytes(ASCII));
		os.write(NEWLINE);
	}

	/**
	 * Send footer of a packet.
	 * @throws IOException
	 */
	public void pacEnd() throws IOException {
		OutputStream os=socket.getOutputStream();
		os.write(PACKAGE_END);
	}

	/**
	 * Send user data, which will be automatically wrapped in a packet.
	 * @param buffer User data
	 * @param recv Receiver account
	 */
	public void pacSendData(byte[] buffer,String recv) {
		try {
			OutputStream os=socket.getOutputStream();
			os.write(PACKAGE_START);
			os.write(recv.getBytes(ASCII));
			os.write(NEWLINE);
			os.write(buffer);
			os.write(PACKAGE_END);
		}
		catch(IOException e){ e.printStackTrace(); }
	}

	/**
	 * Implement this to handle data received.
	 * @param sender Sender account
	 * @param buffer User data
	 */
	public abstract void pacOnDataReceived(String sender,byte[] buffer);

	/**
	 * Start an event loop for response data.
	 * @throws IOException
	 */
	public void pacLoop() throws IOException{
		InputStream is=socket.getInputStream();
		byte[] _mybuffer=new byte[2048]; int sz_mybuffer;
		do{
			int iI,iII,iIII;
			while(mybuffer.size!=0&&(iI=mybuffer.find(PACKAGE_START))!=-1&&(iII=mybuffer.find(PACKAGE_END))!=-1){
				iIII=mybuffer.find(SENDER_SEP,iI+PACKAGE_START.length);
				String sender=new String(mybuffer.buffer,iI+PACKAGE_START.length,iIII-(iI+PACKAGE_START.length));
				byte[] data=new byte[iII-(iIII+SENDER_SEP.length)];
				System.arraycopy(mybuffer.buffer,iIII+SENDER_SEP.length,data,0,data.length);
				this.pacOnDataReceived(sender,data); 
				iII+=PACKAGE_END.length;
				System.arraycopy(mybuffer.buffer,iII,mybuffer.buffer,0,mybuffer.size-=iII);
			}
			if((sz_mybuffer=is.read(_mybuffer))<=0){
				try{Thread.sleep(600);}
				catch(InterruptedException e){ e.printStackTrace(); }
			}
			else if(sz_mybuffer>0&&sz_mybuffer+mybuffer.size<Mybuffer.SZ_BUFFER-1){
				System.arraycopy(_mybuffer,0,mybuffer.buffer,mybuffer.size,sz_mybuffer);
				mybuffer.size+=sz_mybuffer;
			}
			else break;
		} while(true);
	}

	/**
	 * Start an event loop for response data asynchronously.
	 */
	public void pacReceiveAsync(){
		new Thread(){
			@Override
			public void run(){
				try{ pacLoop(); }
				catch(IOException e){ e.printStackTrace(); }
			}
		}.start();
	}
}
