import com.aleozlx.pacswitch.PacswitchClient;
import java.lang.*;
import java.io.*;
import java.util.*;

public class Pactalk{
	public static final String ENC="utf-8";
	public static void main(String[] args) {
		String recv; Console io = System.console();
		if(args.length>=1)recv=args[0];
		else { System.out.println("Usage: java Pactalk receiver"); return; }
		System.out.println("Chatting program using pacswitch protocol. May 2014 (C) Alex");
		System.out.print("Name: ");
		String user=io.readLine();
		System.out.print("Password: ");
		String password=new String(io.readPassword());

		final PacswitchClient cli=new PacswitchClient(){
			@Override
			public void onDataReceived(String sender,byte[] buffer){ 
				try{ 
					System.out.print(sender);
					System.out.print(": ");
					System.out.println(new String(buffer,ENC)); 
				}
				catch(UnsupportedEncodingException e){ }
			}
		};

		if(!cli.pacInit(user,password,"222.69.93.107","pactalk")){ 
			System.out.println("Error: network error"); return; 
		}
		
		cli.start();
		
		Scanner scanner = new Scanner(System.in);
		try{
			while(true){ 
				String s=scanner.nextLine();
				try{ cli.pacSendData(s.getBytes(ENC),recv); }
				catch(UnsupportedEncodingException e){ }
			}
		}
		catch(NoSuchElementException eeof){ /* Raised because of EOF */ }
		finally{ cli.close(); }
	}
}
